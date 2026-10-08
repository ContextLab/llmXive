"""
Data model for a single research subject.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import numpy as np
from pathlib import Path

@dataclass
class Subject:
    """
    Represents a single subject in the study.
    
    Attributes:
        subject_id: Unique identifier for the subject.
        age: Age of the subject in years.
        sex: Sex of the subject (e.g., 'M', 'F').
        pre_motor_score: Motor task score before intervention.
        post_motor_score: Motor task score after intervention.
        improvement_score: Calculated as post_motor_score - pre_motor_score.
        fmri_path: Path to the subject's fMRI data directory.
        confounds_path: Path to the subject's confounds file.
    """
    subject_id: str
    age: int
    sex: str
    pre_motor_score: float
    post_motor_score: float
    fmri_path: Optional[Path] = None
    confounds_path: Optional[Path] = None
    
    @property
    def improvement_score(self) -> float:
        """Calculate the improvement score."""
        return self.post_motor_score - self.pre_motor_score

    def to_dict(self) -> Dict[str, Any]:
        """Convert subject to a dictionary."""
        return {
            'subject_id': self.subject_id,
            'age': self.age,
            'sex': self.sex,
            'pre_motor_score': self.pre_motor_score,
            'post_motor_score': self.post_motor_score,
            'improvement_score': self.improvement_score,
            'fmri_path': str(self.fmri_path) if self.fmri_path else None,
            'confounds_path': str(self.confounds_path) if self.confounds_path else None
        }
