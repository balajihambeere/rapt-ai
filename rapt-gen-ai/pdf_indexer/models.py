from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class IndexingResult:
    """Class to hold the result of indexing operation"""
    success: bool
    paragraphs_indexed: int
    error_message: Optional[str] = None


@dataclass
class IndexingMetadata:
    document_id: str
    date_uploaded: datetime
    title: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None

    def to_dict(self) -> Dict:
        """Convert metadata to dictionary format for Pinecone."""
        return {
            "document_id": self.document_id,
            "date_uploaded": self.date_uploaded.isoformat(),
            "title": self.title,
            "author": self.author,
            "tags": self.tags
        }


