# config.py
import os
from pinecone import Pinecone
import openai


def get_pinecone_index():
    # Initialize Pinecone client
    pc = Pinecone(
        api_key=os.getenv("PINECONE_API_KEY")
    )

    index_name = "raptai-search"

    # Check if index exists, if not create it
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=1536,  # OpenAI ada-002 embedding dimension
            metric='cosine'
        )

    # Get the index
    return pc.Index(index_name)


def initialize_openai():
    openai.api_key = os.getenv("OPENAI_API_KEY")
    return openai


# Export the functions
__all__ = ['get_pinecone_index', 'initialize_openai']
