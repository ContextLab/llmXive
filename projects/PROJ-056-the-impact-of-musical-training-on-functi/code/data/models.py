"""
Data models for the musical training connectivity study.

Defines Subject and ConnectivityMatrix classes with validation against
project schema contracts.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

import numpy as np

from utils.schema_validator import load_schema, validate_record
from pathlib import Path


class ValidationError(Exception):
    """Raised when a data model fails schema validation."""
    pass


@dataclass
class Subject:
    """
    Represents a study participant.
    
    Attributes:
        subject_id: Unique identifier (string)
        group: 'musician' or 'non_musician'
        years_of_training: Total years of musical training (float)
        age: Age in years (float)
        sex: 'M' or 'F'
        motion_score: fMRI motion metric (float)
        ses_score: Socioeconomic status score (float)
    """
    subject_id: str
    group: str
    years_of_training: float
    age: float
    sex: str
    motion_score: float
    ses_score: float
    
    # Internal validation flag
    _validated: bool = field(default=False, repr=False)
    
    def __post_init__(self) -> None:
        """Validate the instance against the subject schema."""
        self._validate()
    
    def _validate(self) -> None:
        """
        Validate Subject attributes against contracts/subject.schema.yaml.
        
        Raises:
            ValidationError: If validation fails.
        """
        # Prepare record for schema validator
        record = {
            "subject_id": self.subject_id,
            "group": self.group,
            "years_of_training": self.years_of_training,
            "age": self.age,
            "sex": self.sex,
            "motion_score": self.motion_score,
            "ses_score": self.ses_score,
        }
        
        # Load schema and validate
        schema_path = Path("contracts/subject.schema.yaml")
        if not schema_path.exists():
            # Fallback to basic validation if schema missing
            self._basic_validation(record)
            self._validated = True
            return
        
        try:
            is_valid, errors = validate_record(record, schema_path)
            if not is_valid:
                raise ValidationError(f"Subject validation failed: {errors}")
            self._validated = True
        except Exception as e:
            # If schema validator fails for any reason, fall back to basic
            self._basic_validation(record)
            self._validated = True
    
    def _basic_validation(self, record: Dict[str, Any]) -> None:
        """
        Basic validation if schema file is missing.
        
        Args:
            record: Dictionary of subject attributes.
        """
        # Validate subject_id format
        if not re.match(r"^[A-Z0-9]{3,}-\d{4}$", record["subject_id"]):
            raise ValidationError(
                f"Invalid subject_id format: {record['subject_id']}. "
                "Expected format: XXX-NNNN"
            )
        
        # Validate group
        valid_groups = {"musician", "non_musician"}
        if record["group"] not in valid_groups:
            raise ValidationError(
                f"Invalid group: {record['group']}. Must be one of {valid_groups}"
            )
        
        # Validate sex
        valid_sex = {"M", "F"}
        if record["sex"] not in valid_sex:
            raise ValidationError(
                f"Invalid sex: {record['sex']}. Must be one of {valid_sex}"
            )
        
        # Validate numeric ranges
        if not 5 <= record["age"] <= 25:
            raise ValidationError(f"Age out of range: {record['age']}")
        
        if record["years_of_training"] < 0:
            raise ValidationError(
                f"Years of training cannot be negative: {record['years_of_training']}"
            )
        
        if record["motion_score"] < 0:
            raise ValidationError(
                f"Motion score cannot be negative: {record['motion_score']}"
            )
        
        if not 0 <= record["ses_score"] <= 1:
            raise ValidationError(
                f"SES score out of range [0, 1]: {record['ses_score']}"
            )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Subject to dictionary."""
        return {
            "subject_id": self.subject_id,
            "group": self.group,
            "years_of_training": self.years_of_training,
            "age": self.age,
            "sex": self.sex,
            "motion_score": self.motion_score,
            "ses_score": self.ses_score,
        }

@dataclass
class ConnectivityMatrix:
    """
    Represents a functional connectivity matrix for a subject.
    
    Attributes:
        subject_id: Reference to the subject
        matrix: 2D numpy array of correlation values (Fisher z-transformed)
        atlas: Name of the atlas used (e.g., 'AAL', 'Schaefer')
        roi_labels: List of ROI names
    """
    subject_id: str
    matrix: np.ndarray
    atlas: str = "AAL"
    roi_labels: Optional[List[str]] = None
    
    def __post_init__(self) -> None:
        """Validate the connectivity matrix."""
        if not isinstance(self.matrix, np.ndarray):
            raise TypeError("matrix must be a numpy.ndarray")
        
        if self.matrix.ndim != 2:
            raise ValueError(f"matrix must be 2D, got {self.matrix.ndim}D")
        
        if self.matrix.shape[0] != self.matrix.shape[1]:
            raise ValueError(
                f"matrix must be square, got shape {self.matrix.shape}"
            )
        
        # Validate symmetry (connectivity matrices should be symmetric)
        if not np.allclose(self.matrix, self.matrix.T, atol=1e-6):
            raise ValueError("Connectivity matrix must be symmetric")
        
        # Validate ROI labels if provided
        if self.roi_labels is not None:
            if len(self.roi_labels) != self.matrix.shape[0]:
                raise ValueError(
                    f"roi_labels length ({len(self.roi_labels)}) "
                    f"must match matrix dimension ({self.matrix.shape[0]})"
                )
    
    def get_edge_list(self) -> List[Dict[str, Any]]:
        """
        Convert matrix to a list of edges (upper triangle).
        
        Returns:
            List of dicts with 'roi_i', 'roi_j', 'strength'.
        """
        edges = []
        n = self.matrix.shape[0]
        roi_labels = self.roi_labels or [f"ROI_{i}" for i in range(n)]
        
        for i in range(n):
            for j in range(i + 1, n):
                edges.append({
                    "roi_i": roi_labels[i],
                    "roi_j": roi_labels[j],
                    "strength": float(self.matrix[i, j]),
                })
        
        return edges

def create_subject_from_dict(data: Dict[str, Any]) -> Subject:
    """
    Factory function to create a Subject from a dictionary.
    
    Args:
        data: Dictionary with subject attributes.
    
    Returns:
        Validated Subject instance.
    """
    required_keys = {
        "subject_id", "group", "years_of_training",
        "age", "sex", "motion_score", "ses_score"
    }
    missing = required_keys - set(data.keys())
    if missing:
        raise KeyError(f"Missing required keys: {missing}")
    
    return Subject(
        subject_id=data["subject_id"],
        group=data["group"],
        years_of_training=float(data["years_of_training"]),
        age=float(data["age"]),
        sex=data["sex"],
        motion_score=float(data["motion_score"]),
        ses_score=float(data["ses_score"]),
    )

def create_subjects_from_dataframe(df: Any) -> List[Subject]:
    """
    Create a list of Subject instances from a pandas DataFrame.
    
    Args:
        df: pandas DataFrame with subject columns.
    
    Returns:
        List of validated Subject instances.
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError("pandas is required for create_subjects_from_dataframe")
    
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")
    
    subjects = []
    for _, row in df.iterrows():
        subjects.append(create_subject_from_dict(row.to_dict()))
    
    return subjects
