"""
Context Configuration Data Model.

Defines the structure for context strategies and their parameters.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum
import hashlib
import json


class StrategyType(Enum):
    """Enumeration of supported context strategies."""
    FIRST_N_LINES = "first_n_lines"
    TF_IDF = "tf_idf"
    DIFF_AWARE = "diff_aware"
    SEMANTIC_SUMMARY = "semantic_summary"


@dataclass
class ContextConfiguration:
    """
    Configuration for a specific context strategy.

    Attributes:
        strategy_type: The type of context strategy to apply.
        max_tokens: Maximum number of tokens to include in the context.
        params: Strategy-specific parameters (e.g., k for TF-IDF, window_size for diff-aware).
        version: Configuration version for reproducibility.
    """
    strategy_type: StrategyType
    max_tokens: int
    params: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0"

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not isinstance(self.strategy_type, StrategyType):
            raise TypeError(f"strategy_type must be a StrategyType enum, got {type(self.strategy_type)}")
        
        if not isinstance(self.max_tokens, int) or self.max_tokens <= 0:
            raise ValueError(f"max_tokens must be a positive integer, got {self.max_tokens}")
        
        if not isinstance(self.params, dict):
            raise TypeError(f"params must be a dictionary, got {type(self.params)}")
        
        if not isinstance(self.version, str):
            raise TypeError(f"version must be a string, got {type(self.version)}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary for serialization."""
        return {
            "strategy_type": self.strategy_type.value,
            "max_tokens": self.max_tokens,
            "params": self.params,
            "version": self.version
        }

    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize configuration to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextConfiguration":
        """Create a ContextConfiguration instance from a dictionary."""
        if "strategy_type" in data and isinstance(data["strategy_type"], str):
            data["strategy_type"] = StrategyType(data["strategy_type"])
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "ContextConfiguration":
        """Create a ContextConfiguration instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def get_config_hash(self) -> str:
        """Generate a deterministic hash of the configuration for caching."""
        config_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ContextConfiguration):
            return NotImplemented
        return (
            self.strategy_type == other.strategy_type and
            self.max_tokens == other.max_tokens and
            self.params == other.params and
            self.version == other.version
        )

    def __hash__(self) -> int:
        return hash((self.strategy_type, self.max_tokens, tuple(sorted(self.params.items())), self.version))
