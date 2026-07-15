from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Type, TypeVar

T = TypeVar('T', bound='SyntheticProblem')

@dataclass
class SyntheticProblem:
    id: str
    premises: List[str]
    operators: List[str]
    solution: str
    entropy_level: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert instance to dictionary."""
        return {
            "id": self.id,
            "premises": self.premises,
            "operators": self.operators,
            "solution": self.solution,
            "entropy_level": self.entropy_level,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create instance from dictionary."""
        return cls(
            id=data["id"],
            premises=data["premises"],
            operators=data["operators"],
            solution=data["solution"],
            entropy_level=data["entropy_level"],
            metadata=data.get("metadata", {})
        )
