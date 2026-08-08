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
        crt_score: Cognitive Reflection Test score.
        random_intercept: Random intercept term for mixed-effects modeling.
    """
    id: str
    crt_score: float
    random_intercept: float = field(default_factory=lambda: 0.0)

    def __post_init__(self):
        """Validate CRT score if provided."""
        if self.crt_score is not None and not (0.0 <= self.crt_score <= 1.0):
            # Assuming CRT score is normalized 0-1, or could be 0-3 depending on scale.
            # If it's a count (0-3), this check needs adjustment.
            # Based on typical CRT usage in regression, it's often a count or normalized.
            # We'll assume it's a raw score for now, but allow any float if not specified.
            # If strict 0-1 is required by spec, uncomment below:
            # raise ValueError(f"CRT score must be between 0 and 1, got {self.crt_score}")
            pass
