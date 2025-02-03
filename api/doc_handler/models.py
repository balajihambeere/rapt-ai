from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class IndexingResult:
    """Class to hold the result of indexing operation"""
    success: bool
    paragraphs_indexed: int
    error_message: Optional[str] = None
