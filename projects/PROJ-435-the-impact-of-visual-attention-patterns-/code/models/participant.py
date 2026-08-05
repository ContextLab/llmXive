"""Participant data model."""
from dataclasses import dataclass, field
from typing import Optional
import numpy as np

@dataclass
class Participant:
    """
    Represents a study participant.

    Attributes:
        id: Unique participant identifier.
        crt_score: Cognitive Reflection Test score.
        random_intercept: Random intercept term for mixed-effects modeling.
    """
    id: str
    crt_score: float
    random_intercept: Optional[float] = None

    def __post_init__(self):
        """Ensure random intercept is initialized if not provided."""
        if self.random_intercept is None:
            self.random_intercept = 0.0

    @staticmethod
    def generate_random_intercept() -> float:
        """Generate a random intercept from a standard normal distribution."""
        return float(np.random.normal(0, 1))
