"""Stimulus (headline) data model."""
from dataclasses import dataclass, field
from typing import Optional
import numpy as np

@dataclass
class Stimulus:
    """
    Represents a headline stimulus.

    Attributes:
        id: Unique stimulus identifier.
        headline_text: The text of the headline.
        valence: Emotional valence score (e.g., from -1 to 1).
        random_intercept: Random intercept term for mixed-effects modeling.
    """
    id: str
    headline_text: str
    valence: Optional[float] = None
    random_intercept: Optional[float] = None

    def __post_init__(self):
        """Ensure optional fields are initialized."""
        if self.valence is None:
            self.valence = 0.0
        if self.random_intercept is None:
            self.random_intercept = 0.0

    @staticmethod
    def generate_random_intercept() -> float:
        """Generate a random intercept from a standard normal distribution."""
        return float(np.random.normal(0, 1))
