"""
Stimulus (Headline) data model.
"""
from dataclasses import dataclass, field
from typing import Optional
import numpy as np


@dataclass
class Stimulus:
    """
    Represents a stimulus (headline) presented to participants.

    Attributes:
        id: Unique identifier for the stimulus.
        headline_text: The text of the headline.
        valence: Emotional valence score (e.g., -1 to 1).
        random_intercept: Random intercept term for mixed-effects modeling.
    """
    id: str
    headline_text: str
    valence: Optional[float] = None
    random_intercept: float = field(default_factory=lambda: 0.0)
