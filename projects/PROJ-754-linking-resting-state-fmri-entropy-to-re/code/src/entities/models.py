"""
Simple data model definitions used by the test suite.
"""
from __future__ import annotations

from dataclasses import dataclass

@dataclass
class Subject:
    """
    Minimal representation of a study participant.

    Attributes
    ----------
    subject_id : str
        Unique identifier for the subject.
    dsrt_score : float
        Domain‑Specific Risk‑Taking score.
    age : int
        Age in years.
    sex : str
        Sex (``"M"`` or ``"F"``).
    mean_fd : float
        Mean framewise displacement (mm).
    """
    subject_id: str
    dsrt_score: float
    age: int
    sex: str
    mean_fd: float
