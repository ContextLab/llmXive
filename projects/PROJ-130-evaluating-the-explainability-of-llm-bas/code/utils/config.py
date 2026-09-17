"""
Research configuration parameters for the llmXive bug fix explainability pipeline.

This module stores hyperparameters and thresholds used across the research scripts.
It is designed to be imported as a singleton configuration object.
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class ResearchConfig:
    """Immutable container for research hyperparameters."""

    # Explainability thresholds
    coherence_threshold: float = 0.6
    """Minimum cosine similarity required for a rationale to be considered coherent."""

    # Model generation parameters
    temperature: float = 0.7
    """Sampling temperature for patch generation."""

    max_tokens: int = 512
    """Maximum number of tokens to generate for patches and rationales."""

    # Additional fixed parameters for consistency
    seed: int = 42
    """Default random seed for reproducibility (overridden by seeding.py if needed)."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary for logging or serialization."""
        return {
            "coherence_threshold": self.coherence_threshold,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "seed": self.seed,
        }

# Global configuration instance
config = ResearchConfig()