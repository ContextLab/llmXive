"""
Stimulus data model.
Represents a headline stimulus with its text and emotional valence.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Stimulus:
    """
    Represents a headline stimulus.

    Attributes:
        id: Unique identifier for the stimulus (headline).
        headline_text: The actual text of the headline.
        valence: Emotional valence score (e.g., from NRC or VADER).
        random_intercept: Random intercept term for mixed-effects modeling.
    """
    id: str
    headline_text: str
    valence: float
    random_intercept: float = 0.0

    def __post_init__(self):
        """Ensure valence and random_intercept are floats."""
        if not isinstance(self.valence, (int, float)):
            self.valence = float(self.valence)
        if not isinstance(self.random_intercept, (int, float)):
            self.random_intercept = float(self.random_intercept)
