"""
Data model for an expert rating of a proposal (T007).
"""
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


VALID_METRICS = ("feasibility", "bottleneck", "alignment")


@dataclass
class Rating:
    """
    Represents an expert's score for a specific proposal on a specific
    metric (feasibility, bottleneck, alignment) on a 1-5 Likert scale.
    """
    rating_id: str
    proposal_id: str
    metric: str
    score: int
    rater_orcid: str
    mock: bool = False
    rated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    _hash: Optional[str] = field(default=None, repr=False, compare=False)

    def __post_init__(self):
        if self.metric not in VALID_METRICS:
            raise ValueError(
                f"metric must be one of {VALID_METRICS}, got {self.metric!r}"
            )
        if not isinstance(self.score, int) or not (1 <= self.score <= 5):
            raise ValueError(f"score must be an integer in [1, 5], got {self.score!r}")
        if self._hash is None:
            content = (
                f"{self.rating_id}|{self.proposal_id}|{self.metric}|"
                f"{self.score}|{self.rater_orcid}"
            )
            self._hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    @property
    def hash(self) -> str:
        return self._hash

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rating_id": self.rating_id,
            "proposal_id": self.proposal_id,
            "metric": self.metric,
            "score": self.score,
            "rater_orcid": self.rater_orcid,
            "mock": self.mock,
            "rated_at": self.rated_at.isoformat(),
            "metadata": self.metadata,
            "hash": self._hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Rating":
        rated_at = (
            datetime.fromisoformat(data["rated_at"])
            if data.get("rated_at")
            else datetime.utcnow()
        )
        return cls(
            rating_id=data["rating_id"],
            proposal_id=data["proposal_id"],
            metric=data["metric"],
            score=int(data["score"]),
            rater_orcid=data["rater_orcid"],
            mock=bool(data.get("mock", False)),
            rated_at=rated_at,
            metadata=data.get("metadata", {}),
            _hash=data.get("hash"),
        )
