from PyPDF2 import PdfReader

from config.config import get_pinecone_index, initialize_openai

openai = initialize_openai()
pinecone_index = get_pinecone_index()


def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text


def generate_embeddings(texts):
    """Generates embeddings for a list of texts using OpenAI's API."""
    response = openai.Embedding.create(
        input=texts,
        model="text-embedding-ada-002"
    )
    return [item['embedding'] for item in response['data']]


def index_texts(pdf_path, metadata):
    """Indexes texts from a PDF file into Pinecone."""
    text = extract_text_from_pdf(pdf_path)
    paragraphs = text.split("\n")  # Splitting into smaller chunks if needed
    embeddings = generate_embeddings(paragraphs)

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
    query_embedding = generate_embeddings([query])[0]
    results = pinecone_index.query(
        query_embedding, top_k=top_k, include_metadata=True)
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
