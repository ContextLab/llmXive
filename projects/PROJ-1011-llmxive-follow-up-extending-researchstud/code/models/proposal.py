"""
Data model for a generated research proposal (T007).
"""
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


VALID_GROUPS = ("pattern-guided", "baseline")


@dataclass
class Proposal:
    """
    Represents a generated research proposal, tagged with its source
    (pattern-guided or baseline) and associated problem statement.
    """
    proposal_id: str
    problem_statement: str
    group_type: str
    text: str
    domain: str
    pattern_ids: List[str] = field(default_factory=list)
    pattern_confidence_scores: List[float] = field(default_factory=list)
    model_name: str = "unknown"
    generated_at: datetime = field(default_factory=datetime.utcnow)
    token_count: int = 0
    generation_time_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    _hash: Optional[str] = field(default=None, repr=False, compare=False)

    def __post_init__(self):
        if self.group_type not in VALID_GROUPS:
            raise ValueError(
                f"group_type must be one of {VALID_GROUPS}, got {self.group_type!r}"
            )
        if self.group_type == "baseline" and self.pattern_ids:
            raise ValueError("baseline proposals must not reference patterns")
        if self.group_type == "pattern-guided" and not self.pattern_ids:
            raise ValueError("pattern-guided proposals require pattern_ids")
        if self._hash is None:
            content = f"{self.proposal_id}|{self.group_type}|{self.text}"
            self._hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    @property
    def hash(self) -> str:
        return self._hash

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "problem_statement": self.problem_statement,
            "group_type": self.group_type,
            "text": self.text,
            "domain": self.domain,
            "pattern_ids": self.pattern_ids,
            "pattern_confidence_scores": self.pattern_confidence_scores,
            "model_name": self.model_name,
            "generated_at": self.generated_at.isoformat(),
            "token_count": self.token_count,
            "generation_time_seconds": self.generation_time_seconds,
            "metadata": self.metadata,
            "hash": self._hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Proposal":
        generated_at = (
            datetime.fromisoformat(data["generated_at"])
            if data.get("generated_at")
            else datetime.utcnow()
        )
        return cls(
            proposal_id=data["proposal_id"],
            problem_statement=data["problem_statement"],
            group_type=data["group_type"],
            text=data["text"],
            domain=data.get("domain", "unknown"),
            pattern_ids=data.get("pattern_ids", []),
            pattern_confidence_scores=data.get("pattern_confidence_scores", []),
            model_name=data.get("model_name", "unknown"),
            generated_at=generated_at,
            token_count=data.get("token_count", 0),
            generation_time_seconds=data.get("generation_time_seconds", 0.0),
            metadata=data.get("metadata", {}),
            _hash=data.get("hash"),
        )
