"""
Participant data model.
Represents a study participant with their cognitive traits and random intercepts.
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
        crt_score: Cognitive Reflection Test score (float).
        random_intercept: Random intercept term for mixed-effects modeling.
    """
    id: str
    crt_score: float
    random_intercept: float = 0.0

    def __post_init__(self):
        """Ensure random_intercept is a float."""
        if not isinstance(self.random_intercept, (int, float)):
            self.random_intercept = float(self.random_intercept)
