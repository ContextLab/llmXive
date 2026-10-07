from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import hashlib
import json

class StrategyType(str, Enum):
    BASELINE = "baseline"
    TFIDF = "tfidf"
    DIFF_AWARE = "diff_aware"
    SEMANTIC_SUMMARY = "semantic_summary"

@dataclass
class ContextConfiguration:
    strategy: StrategyType
    context_window: int
    max_snippets: int
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy.value,
            "context_window": self.context_window,
            "max_snippets": self.max_snippets,
            "params": self.params,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextConfiguration":
        return cls(
            strategy=StrategyType(data["strategy"]),
            context_window=data["context_window"],
            max_snippets=data["max_snippets"],
            params=data.get("params", {}),
        )

    def compute_hash(self) -> str:
        content = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
