import os
from typing import List
from datetime import datetime
import PyPDF2
from tenacity import retry, stop_after_attempt, wait_exponential
from config.config import get_pinecone_index, get_openai_client
from pdf_indexer.exceptions import EmbeddingGenerationError, MetadataValidationError, PDFProcessingError, PineconeUpsertError
from pdf_indexer.models import IndexingMetadata


class PDFIndexer:

    def validate_pdf(self, file_path: str) -> None:
        """Validate if the file is a valid PDF."""
        if not os.path.exists(file_path):
            raise PDFProcessingError(f"File not found: {file_path}")

        if not file_path.lower().endswith('.pdf'):
            raise PDFProcessingError("File must be a PDF")

        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                if len(reader.pages) == 0:
                    return 0
        except PyPDF2.PdfReadError as e:
            raise PDFProcessingError(f"Invalid PDF file: {str(e)}")

    def extract_text(self, file_path: str) -> List[str]:
        """Extract text from PDF and split into paragraphs."""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                paragraphs = []

                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        # Split text into paragraphs (simple implementation)
                        page_paragraphs = [p.strip()
                                           for p in text.split('\n\n') if p.strip()]
                        paragraphs.extend(page_paragraphs)

                return paragraphs
        except Exception as e:
            raise PDFProcessingError(
                f"Error extracting text from PDF: {str(e)}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for the given texts using OpenAI's API."""
        try:
            embeddings = []
            # Process in batches to handle API limits
            batch_size = 100
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                openai_client = get_openai_client()
                response = openai_client.Embedding.create(
                    input=batch,
                    model="text-embedding-ada-002"
                )
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
            return embeddings
        except Exception as e:
            raise EmbeddingGenerationError(
                f"Error generating embeddings: {str(e)}")

    def validate_metadata(self, metadata: IndexingMetadata) -> None:
        """Validate the provided metadata."""
        if not metadata.document_id:
            raise MetadataValidationError("document_id is required")

        if not metadata.date_uploaded:
            raise MetadataValidationError("date_uploaded is required")

        if not isinstance(metadata.date_uploaded, datetime):
            raise MetadataValidationError(
                "date_uploaded must be a datetime object")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def upsert_to_pinecone(self, texts: List[str], embeddings: List[List[float]],
                           metadata: IndexingMetadata) -> None:
        """Upsert the embeddings and metadata to Pinecone."""
        try:
            vectors = []
            base_metadata = metadata.to_dict()

            for i, (text, embedding) in enumerate(zip(texts, embeddings)):
                vector_metadata = {
                    **base_metadata,
                    "text": text,
                    "paragraph_id": i
                }

                vectors.append({
                    "id": f"{metadata.document_id}_p{i}",
                    "values": embedding,
                    "metadata": vector_metadata
                })
            pinecone_index = get_pinecone_index()
            # Upsert in batches
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]

                pinecone_index.upsert(vectors=batch)

        except Exception as e:
            raise PineconeUpsertError(f"Error upserting to Pinecone: {str(e)}")

    def index_texts(self, file_path: str, metadata: IndexingMetadata) -> int:
        """Main function to index texts from a PDF file into Pinecone."""
        try:
            # Validate inputs
            self.validate_pdf(file_path)
            self.validate_metadata(metadata)

            # Extract text
            paragraphs = self.extract_text(file_path)
            if not paragraphs:
                return 0

            # Generate embeddings
            embeddings = self.generate_embeddings(paragraphs)

            # Upsert to Pinecone
            self.upsert_to_pinecone(paragraphs, embeddings, metadata)

            return len(paragraphs)

        except (PDFProcessingError, MetadataValidationError,
                EmbeddingGenerationError, PineconeUpsertError) as e:
            raise e
        except Exception as e:
            raise Exception(f"Unexpected error during indexing: {str(e)}")
