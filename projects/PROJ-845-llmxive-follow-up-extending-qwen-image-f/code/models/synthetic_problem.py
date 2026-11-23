from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Type, TypeVar
import json

T = TypeVar('T', bound='SyntheticProblem')

@dataclass
class SyntheticProblem:
    """Represents a synthetic logic/arithmetic problem."""
    id: str
    premises: List[str]
    operators: List[str]
    solution: str
    entropy_level: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
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
            id=data.get("id", ""),
            premises=data.get("premises", []),
            operators=data.get("operators", []),
            solution=data.get("solution", ""),
            entropy_level=data.get("entropy_level", "unknown"),
            metadata=data.get("metadata", {})
        )
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls: Type[T], json_str: str) -> T:
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))