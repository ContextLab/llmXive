from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json
import hashlib

@dataclass
class SyntheticProblem:
    id: str
    premises: List[str]
    operators: List[str]
    solution: str
    entropy_level: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "premises": self.premises,
            "operators": self.operators,
            "solution": self.solution,
            "entropy_level": self.entropy_level,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyntheticProblem":
        return cls(
            id=data["id"],
            premises=data["premises"],
            operators=data["operators"],
            solution=data["solution"],
            entropy_level=data["entropy_level"],
            metadata=data.get("metadata", {})
        )
