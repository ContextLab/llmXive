"""
Data model for an expert rating of a proposal.
"""
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

@dataclass
class Rating:
    """
    Represents a single expert rating for a proposal.
    """
    rating_id: str
    proposal_id: str
    rater_orcid: str  # Blinded ORCID or anonymized ID
    feasibility_score: float  # 1-5 scale
    bottleneck_score: float  # 1-5 scale
    alignment_score: float  # 1-5 scale
    comments: Optional[str] = None
    rated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    _hash: Optional[str] = field(default=None, repr=False, compare=False)

    def __post_init__(self):
        """Generate a deterministic hash for the record."""
        if self._hash is None:
            content = f"{self.rating_id}|{self.proposal_id}|{self.rater_orcid}|{self.feasibility_score}|{self.bottleneck_score}|{self.alignment_score}"
            self._hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

    @property
    def hash(self) -> str:
        return self._hash

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "rating_id": self.rating_id,
            "proposal_id": self.proposal_id,
            "rater_orcid": self.rater_orcid,
            "feasibility_score": self.feasibility_score,
            "bottleneck_score": self.bottleneck_score,
            "alignment_score": self.alignment_score,
            "comments": self.comments,
            "rated_at": self.rated_at.isoformat(),
            "metadata": self.metadata,
            "hash": self._hash
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Rating":
        """Construct from a dictionary."""
        rated_at = datetime.fromisoformat(data["rated_at"]) if data.get("rated_at") else datetime.utcnow()

        return cls(
            rating_id=data["rating_id"],
            proposal_id=data["proposal_id"],
            rater_orcid=data["rater_orcid"],
            feasibility_score=data["feasibility_score"],
            bottleneck_score=data["bottleneck_score"],
            alignment_score=data["alignment_score"],
            comments=data.get("comments"),
            rated_at=rated_at,
            metadata=data.get("metadata", {}),
            _hash=data.get("hash")
        )