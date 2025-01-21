
import os
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI


def get_pinecone_index():
    # Initialize Pinecone client
    pc = Pinecone(
        api_key="pcsk_6XfhvG_NKcbiSxh1fCZN7wCC3o92VA3kgN5PPsGLBdTuMyEYzVkGxV2spg46YczYdy5AiZ"
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
    return OpenAI(
        api_key="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"
    )


# Export the functions
__all__ = ['get_pinecone_index', 'initialize_openai']
