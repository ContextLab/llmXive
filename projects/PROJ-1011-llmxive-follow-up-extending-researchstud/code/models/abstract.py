"""
Data model for a scientific abstract.
"""
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

@dataclass
class Abstract:
    """
    Represents a single scientific abstract from a corpus.
    """
    title: str
    abstract_text: str
    venue: str
    domain: str  # e.g., 'ML', 'Public Health', 'Climate'
    acceptance_status: str  # 'accepted', 'rejected', 'unknown'
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    published_date: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    _hash: Optional[str] = field(default=None, repr=False, compare=False)

    def __post_init__(self):
        """Generate a deterministic hash for the record."""
        if self._hash is None:
            content = f"{self.title}|{self.abstract_text}|{self.venue}|{self.domain}|{self.acceptance_status}|{self.doi or ''}|{self.arxiv_id or ''}"
            self._hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

    @property
    def hash(self) -> str:
        return self._hash

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "abstract_text": self.abstract_text,
            "venue": self.venue,
            "domain": self.domain,
            "acceptance_status": self.acceptance_status,
            "doi": self.doi,
            "arxiv_id": self.arxiv_id,
            "published_date": self.published_date.isoformat() if self.published_date else None,
            "metadata": self.metadata,
            "hash": self._hash
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Abstract":
        """Construct from a dictionary."""
        pub_date = None
        if data.get("published_date"):
            pub_date = datetime.fromisoformat(data["published_date"])

        return cls(
            title=data["title"],
            abstract_text=data["abstract_text"],
            venue=data["venue"],
            domain=data["domain"],
            acceptance_status=data["acceptance_status"],
            doi=data.get("doi"),
            arxiv_id=data.get("arxiv_id"),
            published_date=pub_date,
            metadata=data.get("metadata", {}),
            _hash=data.get("hash")
        )
