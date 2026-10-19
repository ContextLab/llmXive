"""
Data model for a generated research proposal.
"""
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

@dataclass
class Proposal:
    """
    Represents a single generated research proposal.

    Attributes
    ----------
    proposal_id : str
        Deterministic identifier for the proposal (UUID‑like hash).
    problem_statement : str
        The problem statement extracted from the source abstract.
    group_type : str
        Either ``pattern-guided`` or ``baseline`` indicating the generation mode.
    text : str
        Full generated proposal text.
    patterns_used : Optional[List[str]]
        List of pattern IDs injected into the prompt (only for pattern‑guided proposals).
    pattern_confidence_scores : Optional[List[float]]
        Cosine similarity scores (or other confidence) for the injected patterns.
    generation_metadata : Dict[str, Any]
        Arbitrary metadata produced by the LLM generation step (model name, timestamps,
        token usage, etc.).
    created_at : datetime
        Timestamp when the proposal was generated.
    metadata : Dict[str, Any]
        Additional free‑form metadata that may be added downstream.
    _hash : Optional[str]
        Internal deterministic hash of the immutable fields; generated on demand.
    """

    proposal_id: str
    problem_statement: str
    group_type: str  # 'pattern-guided' or 'baseline'
    text: str
    patterns_used: Optional[List[str]] = field(default_factory=list)
    pattern_confidence_scores: Optional[List[float]] = field(default_factory=list)
    generation_metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    _hash: Optional[str] = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Generate a deterministic hash if not supplied."""
        if self._hash is None:
            # Use stable fields only; exclude mutable metadata that may change over time
            hash_input = (
                f"{self.proposal_id}|"
                f"{self.problem_statement}|"
                f"{self.group_type}|"
                f"{self.text}"
            )
            self._hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()

    @property
    def hash(self) -> str:
        """Public accessor for the deterministic hash."""
        return self._hash

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the proposal to a plain dictionary suitable for JSONL output."""
        return {
            "proposal_id": self.proposal_id,
            "problem_statement": self.problem_statement,
            "group_type": self.group_type,
            "text": self.text,
            "patterns_used": self.patterns_used,
            "pattern_confidence_scores": self.pattern_confidence_scores,
            "generation_metadata": self.generation_metadata,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            "hash": self._hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Proposal":
        """Re‑create a Proposal instance from a dictionary (e.g. loaded from JSONL)."""
        created_at = (
            datetime.fromisoformat(data["created_at"])
            if isinstance(data.get("created_at"), str)
            else datetime.utcnow()
        )

        return cls(
            proposal_id=data["proposal_id"],
            problem_statement=data["problem_statement"],
            group_type=data["group_type"],
            text=data["text"],
            patterns_used=data.get("patterns_used", []),
            pattern_confidence_scores=data.get(
                "pattern_confidence_scores", []
            ),
            generation_metadata=data.get("generation_metadata", {}),
            created_at=created_at,
            metadata=data.get("metadata", {}),
            _hash=data.get("hash"),
        )
