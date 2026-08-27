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
    Represents a research proposal, either pattern-guided or baseline.
    """
    proposal_id: str
    problem_statement: str
    proposal_text: str
    generation_type: str  # 'pattern_guided' or 'baseline'
    pattern_id: Optional[str] = None  # If pattern_guided, reference the pattern
    model_used: Optional[str] = None
    generation_timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    _hash: Optional[str] = field(default=None, repr=False, compare=False)

    def __post_init__(self):
        """Generate a deterministic hash for the record."""
        if self._hash is None:
            content = f"{self.proposal_id}|{self.problem_statement}|{self.proposal_text}|{self.generation_type}|{self.pattern_id or ''}"
            self._hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

    @property
    def hash(self) -> str:
        return self._hash

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "proposal_id": self.proposal_id,
            "problem_statement": self.problem_statement,
            "proposal_text": self.proposal_text,
            "generation_type": self.generation_type,
            "pattern_id": self.pattern_id,
            "model_used": self.model_used,
            "generation_timestamp": self.generation_timestamp.isoformat(),
            "metadata": self.metadata,
            "hash": self._hash
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Proposal":
        """Construct from a dictionary."""
        gen_time = datetime.fromisoformat(data["generation_timestamp"]) if data.get("generation_timestamp") else datetime.utcnow()

        return cls(
            proposal_id=data["proposal_id"],
            problem_statement=data["problem_statement"],
            proposal_text=data["proposal_text"],
            generation_type=data["generation_type"],
            pattern_id=data.get("pattern_id"),
            model_used=data.get("model_used"),
            generation_timestamp=gen_time,
            metadata=data.get("metadata", {}),
            _hash=data.get("hash")
        )
