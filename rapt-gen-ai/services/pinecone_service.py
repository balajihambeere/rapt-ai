import traceback
from PyPDF2 import PdfReader
from typing import List, Union
import time
from config.config import get_pinecone_index, initialize_openai
import sys
sys.setrecursionlimit(10000)


def debug_log(message):
    print(message)
    traceback.print_stack()


client = initialize_openai()
pinecone_index = get_pinecone_index()

# Define constants for the Pinecone index, namespace, and engine
ENGINE = 'text-embedding-3-small'


def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

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

# Function to get embedding for a single text using the OpenAI API


# def get_embedding(text, engine=ENGINE):
#     # Use the get_embeddings function to get the embedding for a single text
#     return get_embeddings([text], engine)[0]


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
