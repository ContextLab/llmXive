"""
Data model for a single research subject.

Encapsulates subject demographics, behavioral scores, and preprocessing metadata.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import numpy as np
from pathlib import Path


@dataclass
class Subject:
    """
    Represents a single participant in the motor memory consolidation study.

    Attributes:
        subject_id (str): Unique identifier (e.g., 'sub-01').
        age (int): Age in years.
        sex (str): Biological sex ('M' or 'F').
        pre_score (float): Pre-training behavioral score.
        post_score (float): Post-training behavioral score.
        improvement (float): Calculated improvement (post - pre).
        mean_fd (float): Mean Framewise Displacement from fMRIPrep.
        excluded (bool): Flag indicating if subject was excluded from analysis.
        exclusion_reason (Optional[str]): Reason for exclusion if applicable.
        raw_data_path (Optional[Path]): Path to the subject's raw/preprocessed directory.
    """
    subject_id: str
    age: Optional[int] = None
    sex: Optional[str] = None
    pre_score: Optional[float] = None
    post_score: Optional[float] = None
    improvement: Optional[float] = None
    mean_fd: Optional[float] = None
    excluded: bool = False
    exclusion_reason: Optional[str] = None
    raw_data_path: Optional[Path] = None

    def __post_init__(self):
        """Calculate improvement score if both pre and post scores are available."""
        if self.pre_score is not None and self.post_score is not None:
            self.improvement = float(self.post_score - self.pre_score)

    def validate(self, fd_threshold: float = 0.2) -> bool:
        """
        Validate subject data against quality thresholds.

        Args:
            fd_threshold: Maximum allowed mean Framewise Displacement.

        Returns:
            bool: True if subject is valid, False otherwise.
        """
        if self.pre_score is None or self.post_score is None:
            self.excluded = True
            self.exclusion_reason = "Missing behavioral scores"
            return False

        if self.mean_fd is not None and self.mean_fd > fd_threshold:
            self.excluded = True
            self.exclusion_reason = f"Mean FD ({self.mean_fd:.3f}) exceeds threshold ({fd_threshold})"
            return False

        if self.age is None:
            self.excluded = True
            self.exclusion_reason = "Missing age"
            return False

        if self.sex is None:
            self.excluded = True
            self.exclusion_reason = "Missing sex"
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert subject to a dictionary for serialization."""
        return {
            'subject_id': self.subject_id,
            'age': self.age,
            'sex': self.sex,
            'pre_score': self.pre_score,
            'post_score': self.post_score,
            'improvement': self.improvement,
            'mean_fd': self.mean_fd,
            'excluded': self.excluded,
            'exclusion_reason': self.exclusion_reason
        }
