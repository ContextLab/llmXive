"""
Participant data model.
"""
from dataclasses import dataclass, field
from typing import Optional
import numpy as np


@dataclass
class Participant:
    """
    Represents a study participant.

    Attributes:
        id: Unique identifier for the participant.
        crt_score: Cognitive Reflection Test score (normalized 0.0 to 1.0).
        random_intercept: Random intercept term for mixed-effects modeling.
    """
    id: str
    crt_score: float
    random_intercept: float = field(default_factory=lambda: 0.0)

    def __post_init__(self):
        """Validate CRT score if provided."""
        if self.crt_score is not None:
            if not (0.0 <= self.crt_score <= 1.0):
                # Assuming CRT score is normalized 0-1.
                # If the source data provides raw counts (e.g., 0-3), this validation
                # should be adjusted or the data should be normalized upstream.
                # For now, we strictly enforce the 0-1 range as per the model contract.
                raise ValueError(f"CRT score must be between 0.0 and 1.0, got {self.crt_score}")

    def to_dict(self) -> dict:
        """Convert the participant instance to a dictionary."""
        return {
            "id": self.id,
            "crt_score": self.crt_score,
            "random_intercept": self.random_intercept
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Participant":
        """Create a Participant instance from a dictionary."""
        return cls(
            id=data["id"],
            crt_score=float(data["crt_score"]),
            random_intercept=float(data.get("random_intercept", 0.0))
        )