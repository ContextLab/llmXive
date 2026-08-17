"""
Data models for the project.
Implements T007: Create base data models (Subject, ConnectivityMatrix).
"""
from __future__ import annotations
import re
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import numpy as np

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Raised when data validation fails."""
    pass

@dataclass
class Subject:
    """
    Represents a single subject in the study.
    Validates against contracts/subject.schema.yaml logic.
    """
    subject_id: str
    group: str  # 'musician' or 'non_musician'
    years_of_training: float
    age: float
    sex: str  # 'M' or 'F'
    motion_score: float
    ses_score: float

    def __post_init__(self):
        """Validate the subject data."""
        if not self.subject_id:
            raise ValidationError("subject_id cannot be empty")
        
        if self.group not in ['musician', 'non_musician']:
            raise ValidationError(f"Invalid group: {self.group}. Must be 'musician' or 'non_musician'.")
        
        if self.years_of_training < 0:
            raise ValidationError("years_of_training cannot be negative")
        
        if self.age < 0 or self.age > 120:
            raise ValidationError(f"Invalid age: {self.age}")
        
        if self.sex not in ['M', 'F']:
            raise ValidationError(f"Invalid sex: {self.sex}. Must be 'M' or 'F'.")
        
        if self.motion_score < 0:
            raise ValidationError("motion_score cannot be negative")
        
        if self.ses_score < 0:
            raise ValidationError("ses_score cannot be negative")

    def to_dict(self) -> Dict[str, Any]:
        """Convert subject to dictionary."""
        return {
            'subject_id': self.subject_id,
            'group': self.group,
            'years_of_training': self.years_of_training,
            'age': self.age,
            'sex': self.sex,
            'motion_score': self.motion_score,
            'ses_score': self.ses_score
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Subject:
        """Create a Subject from a dictionary."""
        return cls(
            subject_id=data['subject_id'],
            group=data['group'],
            years_of_training=data['years_of_training'],
            age=data['age'],
            sex=data['sex'],
            motion_score=data['motion_score'],
            ses_score=data['ses_score']
        )

@dataclass
class ConnectivityMatrix:
    """
    Represents a functional connectivity matrix for a subject.
    """
    subject_id: str
    matrix: np.ndarray  # 2D array of correlation values
    atlas: str = "Schaefer"  # Default atlas
    n_rois: int = field(init=False)

    def __post_init__(self):
        """Validate the connectivity matrix."""
        if not isinstance(self.matrix, np.ndarray):
            raise ValidationError("matrix must be a numpy array")
        
        if self.matrix.ndim != 2:
            raise ValidationError("matrix must be 2D")
        
        if self.matrix.shape[0] != self.matrix.shape[1]:
            raise ValidationError("matrix must be square")
        
        # Validate correlation values are between -1 and 1
        if np.any(self.matrix < -1.0) or np.any(self.matrix > 1.0):
            logger.warning(f"Matrix for {self.subject_id} contains values outside [-1, 1]. Clipping.")
            self.matrix = np.clip(self.matrix, -1.0, 1.0)
        
        self.n_rois = self.matrix.shape[0]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (matrix as list of lists for JSON compatibility)."""
        return {
            'subject_id': self.subject_id,
            'atlas': self.atlas,
            'matrix': self.matrix.tolist()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConnectivityMatrix:
        """Create from dictionary."""
        matrix = np.array(data['matrix'])
        return cls(
            subject_id=data['subject_id'],
            matrix=matrix,
            atlas=data.get('atlas', 'Schaefer')
        )

def create_subject_from_dict(data: Dict[str, Any]) -> Subject:
    """Helper to create a Subject from a dict, handling validation."""
    return Subject.from_dict(data)

def create_subjects_from_dataframe(df: pd.DataFrame) -> List[Subject]:
    """
    Create a list of Subject objects from a pandas DataFrame.
    
    Args:
        df: DataFrame with columns matching Subject fields.
    
    Returns:
        List of Subject instances.
    
    Raises:
        ValidationError: If any row fails validation.
    """
    import pandas as pd
    subjects = []
    for idx, row in df.iterrows():
        try:
            sub = Subject(
                subject_id=str(row['subject_id']),
                group=row['group'],
                years_of_training=float(row['years_of_training']),
                age=float(row['age']),
                sex=row['sex'],
                motion_score=float(row['motion_score']),
                ses_score=float(row['ses_score'])
            )
            subjects.append(sub)
        except ValidationError as e:
            logger.error(f"Validation error at row {idx}: {e}")
            raise
    return subjects
