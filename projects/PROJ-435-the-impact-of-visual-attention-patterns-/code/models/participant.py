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
    random_intercept: float = field(default_factory=lambda: np.random.normal(0, 1))

    def __post_init__(self):
        """Ensure CRT score is numeric."""
        if not isinstance(self.crt_score, (int, float)):
            raise TypeError("crt_score must be a numeric value")
