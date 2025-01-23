import os
from typing import List
from datetime import datetime
import time
import PyPDF2
from tenacity import retry, stop_after_attempt, wait_exponential
from config.config import get_openai_client, get_pinecone_index
import spacy
import pytesseract
from PIL import Image

from doc_handler.exceptions import EmbeddingGenerationError, MetadataValidationError, PDFProcessingError, PineconeUpsertError
from doc_handler.models import IndexingResult
from models.metadata import Metadata


class DocumentRetrieval:
    def __init__(self):
        # Initialize your document retrieval system
        self.nlp = spacy.load("en_core_web_sm")  # Load spaCy model for NER
        pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'  # Path to tesseract executable

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

    def extract_text_with_ocr(self, file_path: str) -> List[str]:
        """Extract text from images in PDF using OCR."""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                paragraphs = []

                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if not text:
                        # If no text is found, use OCR
                        page_image = self.convert_pdf_page_to_image(file_path, page_num)
                        text = pytesseract.image_to_string(page_image)
                    
                    if text:
                        page_paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                        paragraphs.extend(page_paragraphs)

                return paragraphs
        except Exception as e:
            raise PDFProcessingError(f"Error extracting text from PDF: {str(e)}")

    def convert_pdf_page_to_image(self, file_path: str, page_num: int) -> Image:
        """Convert a specific page of a PDF to an image."""
        from pdf2image import convert_from_path
        images = convert_from_path(file_path, first_page=page_num+1, last_page=page_num+1)
        return images[0]

    def perform_ner(self, text: str) -> List[str]:
        """Perform Named Entity Recognition (NER) on the given text."""
        doc = self.nlp(text)
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        return entities

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
                response = openai_client.embeddings.create(
                    input=batch,
                    model="text-embedding-ada-002"
                )
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
            return embeddings
        except Exception as e:
            raise EmbeddingGenerationError(
                f"Error generating embeddings: {str(e)}")

    def validate_metadata(self, metadata: Metadata) -> None:
        """Validate the provided metadata."""
        if not metadata['document_id']:
            raise MetadataValidationError("document_id is required")

        if not metadata['date_uploaded']:
            raise MetadataValidationError("date_uploaded is required")

        # if not isinstance(metadata['date_uploaded'], datetime):
        #     raise MetadataValidationError(
        #         "date_uploaded must be a datetime object")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def upsert_to_pinecone(self, texts: List[str], embeddings: List[List[float]], metadata: Metadata) -> None:
        """Upsert the embeddings and metadata to Pinecone."""
        try:
            vectors = []

            for i, (text, embedding) in enumerate(zip(texts, embeddings)):
                vector_metadata = {
                    **metadata,
                    "text": text,
                    "paragraph_id": i
                }
                vectors.append({
                    "id": f"{metadata['document_id']}_p{i}",
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

    def index_texts(self, file_path: str, metadata: Metadata) -> int:
        """Main function to index texts from a PDF file into Pinecone."""
        try:
            # Validate inputs
            self.validate_pdf(file_path)
            self.validate_metadata(metadata)

            # Extract text
            paragraphs = self.extract_text_with_ocr(file_path)
            if not paragraphs:
                return 0

            # Perform NER on extracted text
            for paragraph in paragraphs:
                entities = self.perform_ner(paragraph)
                print(f"Entities in paragraph: {entities}")

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

    def query_index(self, query, top_k=5):
        """Queries the Pinecone index for similar texts."""
        query_embedding = self.generate_embeddings([query])[0]

        pinecone_index = get_pinecone_index()

        results = pinecone_index.query(
            vector=query_embedding, top_k=top_k, include_metadata=True)
        return results["matches"]
