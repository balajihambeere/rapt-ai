import os
import PyPDF2
from config.config import get_pinecone_index, initialize_openai


client = initialize_openai()
pinecone_index = get_pinecone_index()

# Define constants for the Pinecone index, namespace, and engine
ENGINE = 'text-embedding-3-small'


def extract_text_from_pdf(file_path):
    """
    Extracts text from a PDF file, handling various edge cases as specified in the user stories.

    :param file_path: Path to the PDF file
    :return: Extracted text as a string
    :raises: ValueError, FileNotFoundError, or RuntimeError depending on the issue
    """
    # Check if file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file at path '{file_path}' does not exist.")

    # Check if the file is a valid PDF
    if not file_path.lower().endswith('.pdf'):
        raise ValueError(f"The file '{file_path}' is not a valid PDF.")

    try:
        # Open the PDF file
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)

            # Check if PDF contains any pages
            if not reader.pages:
                return ""  # Return an empty string for PDFs with no text

            # Extract text from all pages
            extracted_text = ""
            for page in reader.pages:
                extracted_text += page.extract_text() or ""

            return extracted_text

    except PyPDF2.errors.PdfReadError:
        raise ValueError(f"The file '{file_path}' is not a readable PDF.")

    except MemoryError:
        raise RuntimeError("The file is too large to process with the available memory.")


# Function to get embeddings for a list of texts using the OpenAI API
def get_embeddings(texts, engine=ENGINE):
    # Validate input
    if not isinstance(texts, list) or not all(isinstance(t, str) for t in texts):
        raise ValueError("Input texts must be a list of strings.")

    # Avoid nested calls
    if any(isinstance(t, list) for t in texts):
        raise ValueError("Nested lists are not allowed.")

    # Create embeddings for the input texts using the specified engine
    response = client.embeddings.create(
        input=texts,
        model=engine
    )

    # Extract and return the list of embeddings from the response
    return [d.embedding for d in list(response.data)]



def index_texts(pdf_path, metadata):
    """Indexes texts from a PDF file into Pinecone."""
    text = extract_text_from_pdf(pdf_path)
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    # print('paragraphs', paragraphs)
    embeddings = get_embeddings(paragraphs, engine=ENGINE)

    # time.sleep(10)

    # Prepare data for upserting
    data = [
        {"id": f"{metadata['document_id']}-{i}", "values": embeddings[i], "metadata": {
            "text": paragraphs[i],
            "date_uploaded": metadata["date_uploaded"]
        }}
        for i in range(len(paragraphs))
    ]

    # Upsert into Pinecone
    pinecone_index.upsert(vectors=data)
    return len(data)


def query_index(query, top_k=5):
    """Queries the Pinecone index for similar texts."""
    query_embedding = get_embeddings([query])[0]

    results = pinecone_index.query(
        vector=query_embedding, top_k=top_k, include_metadata=True)
    return results["matches"]


def delete_texts_from_index(text_ids):
    """Deletes texts from the Pinecone index by their IDs."""
    pinecone_index.delete(ids=text_ids)


def batch_upload_texts(pdf_paths, metadata_list, batch_size=10):
    """Uploads texts to the Pinecone index in batches."""
    total_uploaded = 0
    for i in range(0, len(pdf_paths), batch_size):
        batch = pdf_paths[i:i+batch_size]
        for j, pdf_path in enumerate(batch):
            metadata = metadata_list[i + j]
            total_uploaded += index_texts(pdf_path, metadata)
    return total_uploaded
