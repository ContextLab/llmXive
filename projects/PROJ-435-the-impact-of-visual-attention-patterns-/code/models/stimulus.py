"""
Stimulus data model.

Represents a headline stimulus with its text, valence score,
and random intercept for mixed-effects modeling.
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
        valence: Valence score of the headline (e.g., from NRC or VADER).
        random_intercept: Random intercept value for mixed-effects modeling.
    """
    id: str
    headline_text: str
    valence: float = 0.0
    random_intercept: float = 0.0

    def __post_init__(self):
        """Ensure valence and random_intercept are floats."""
        if not isinstance(self.valence, (int, float)):
            try:
                self.valence = float(self.valence)
            except (ValueError, TypeError):
                raise ValueError(f"Invalid valence score: {self.valence}")
        
        if not isinstance(self.random_intercept, (int, float)):
            self.random_intercept = float(self.random_intercept)
