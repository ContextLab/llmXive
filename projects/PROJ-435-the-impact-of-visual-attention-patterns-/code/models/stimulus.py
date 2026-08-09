"""
Stimulus (Headline) data model.

Represents a stimulus (headline) presented to participants in the eye-tracking study.
"""
from dataclasses import dataclass, field
from typing import Optional
import numpy as np


@dataclass
class Stimulus:
    """
    Represents a stimulus (headline) presented to participants.

    Attributes:
        id: Unique identifier for the stimulus (e.g., 'headline_001').
        headline_text: The full text content of the headline.
        valence: Emotional valence score (typically -1.0 to 1.0), calculated from
                 NRC or VADER lexicons. Optional until T021 computes it.
        random_intercept: Random intercept term for mixed-effects modeling to account
                          for stimulus-specific variance. Initialized to 0.0.
    """
    id: str
    headline_text: str
    valence: Optional[float] = None
    random_intercept: float = field(default_factory=lambda: 0.0)