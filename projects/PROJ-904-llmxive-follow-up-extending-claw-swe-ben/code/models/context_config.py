"""
Context Configuration Data Model.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import hashlib
import json

class StrategyType(Enum):
    BASELINE = "baseline"
    TFIDF = "tfidf"
    DIFF_AWARE = "diff_aware"
    SEMANTIC_SUMMARY = "semantic_summary"

@dataclass
class ContextConfiguration:
    strategy: StrategyType
    snippets: List[Any] = field(default_factory=list)
    max_tokens: int = 4096

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy.value,
            "snippets_count": len(self.snippets),
            "max_tokens": self.max_tokens
        }
