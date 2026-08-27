"""
Data model for a research ideation pattern.
"""
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

@dataclass
class PatternCard:
    """
    Represents an ideation pattern derived from ML literature.
    """
    pattern_id: str
    title: str
    description: str
    problem_domain: str  # e.g., 'Climate Adaptation'
    solution_strategy: str  # e.g., 'Transfer Learning', 'Synthetic Data'
    key_components: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    source_references: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    _hash: Optional[str] = field(default=None, repr=False, compare=False)

    def __post_init__(self):
        """Generate a deterministic hash for the record."""
        if self._hash is None:
            content = f"{self.pattern_id}|{self.title}|{self.description}|{self.problem_domain}|{self.solution_strategy}"
            self._hash = hashlib.sha256(content.encode('utf-8')).hexdigest()

    @property
    def hash(self) -> str:
        return self._hash

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "pattern_id": self.pattern_id,
            "title": self.title,
            "description": self.description,
            "problem_domain": self.problem_domain,
            "solution_strategy": self.solution_strategy,
            "key_components": self.key_components,
            "examples": self.examples,
            "source_references": self.source_references,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            "hash": self._hash
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PatternCard":
        """Construct from a dictionary."""
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow()

        return cls(
            pattern_id=data["pattern_id"],
            title=data["title"],
            description=data["description"],
            problem_domain=data["problem_domain"],
            solution_strategy=data["solution_strategy"],
            key_components=data.get("key_components", []),
            examples=data.get("examples", []),
            source_references=data.get("source_references", []),
            tags=data.get("tags", []),
            created_at=created_at,
            metadata=data.get("metadata", {}),
            _hash=data.get("hash")
        )
