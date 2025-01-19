
import os
from pinecone import Pinecone, ServerlessSpec
import openai


def get_pinecone_index():
    # Initialize Pinecone client
    pc = Pinecone(
        api_key="PINECONE_API_KEY"
    )

    index_name = "raptai-search"

    # Check if index exists, if not create it
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=1536,  # OpenAI ada-002 embedding dimension
            metric='cosine',
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'  # or your preferred AWS region
            )
        )

    # Get the index
    return pc.Index(index_name)


def initialize_openai():
    openai.api_key = "OPENAI_API_KEY"
    return openai


# Export the functions
__all__ = ['get_pinecone_index', 'initialize_openai']
