"""Stimulus (headline) data model."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Stimulus:
    """
    Represents a visual stimulus (headline).

    Attributes:
        id: Unique stimulus identifier.
        headline_text: The text of the headline.
        valence: Emotional valence score (e.g., from NRC or VADER).
        random_intercept: Random intercept term for mixed-effects modeling.
    """
    id: str
    headline_text: str
    valence: Optional[float] = None
    random_intercept: float = 0.0

    def __post_init__(self):
        """Validate headline text."""
        if not self.headline_text or not isinstance(self.headline_text, str):
            raise ValueError("headline_text must be a non-empty string")
