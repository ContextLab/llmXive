from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

import numpy as np

from utils.schema_validator import load_schema, validate_record

class ValidationError(Exception):
    """Custom exception for data validation failures."""
    pass

@dataclass
class Subject:
    """
    Represents a subject in the study with demographic and training attributes.
    
    Attributes:
        subject_id: Unique identifier for the subject.
        group: Group assignment ('musician' or 'non_musician').
        years_of_training: Years of musical training (0 for non-musicians).
        age: Age in years.
        sex: Biological sex ('M' or 'F').
        motion_score: Average motion score from fMRI preprocessing.
        ses_score: Socioeconomic status score.
    """
    subject_id: str
    group: str
    years_of_training: float
    age: float
    sex: str
    motion_score: float
    ses_score: float

    def __post_init__(self):
        """Validate the subject instance against the schema."""
        self._validate()

    def _validate(self) -> None:
        """
        Validates the instance attributes against the contracts/subject.schema.yaml.
        Raises ValidationError if validation fails.
        """
        # Construct a dictionary representation for validation
        record = {
            'subject_id': self.subject_id,
            'group': self.group,
            'years_of_training': self.years_of_training,
            'age': self.age,
            'sex': self.sex,
            'motion_score': self.motion_score,
            'ses_score': self.ses_score
        }

        try:
            # Load the schema from the contracts directory
            schema = load_schema('contracts/subject.schema.yaml')
            # Validate the record
            is_valid, errors = validate_record(schema, record)
            
            if not is_valid:
                error_details = "; ".join(errors) if isinstance(errors, list) else str(errors)
                raise ValidationError(f"Subject validation failed: {error_details}")
            
            # Additional runtime checks that might not be covered by schema or for specific business logic
            if self.group not in ('musician', 'non_musician'):
                raise ValidationError(f"Invalid group '{self.group}'. Must be 'musician' or 'non_musician'.")
            
            if self.sex not in ('M', 'F'):
                raise ValidationError(f"Invalid sex '{self.sex}'. Must be 'M' or 'F'.")
                
            if self.years_of_training < 0:
                raise ValidationError(f"Years of training cannot be negative.")
                
            if self.age <= 0:
                raise ValidationError(f"Age must be positive.")

        except FileNotFoundError:
            # If schema is missing, we might skip validation or raise a specific warning
            # For this implementation, we assume the schema exists as per T004
            raise ValidationError("Validation schema 'contracts/subject.schema.yaml' not found.")

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Subject instance to a dictionary."""
        return {
            'subject_id': self.subject_id,
            'group': self.group,
            'years_of_training': self.years_of_training,
            'age': self.age,
            'sex': self.sex,
            'motion_score': self.motion_score,
            'ses_score': self.ses_score
        }

@dataclass
class ConnectivityMatrix:
    """
    Represents a functional connectivity matrix for a subject.
    
    Attributes:
        subject_id: Unique identifier linking to the Subject.
        matrix: 2D numpy array representing the connectivity matrix (Pearson correlations).
        roi_labels: List of ROI labels corresponding to the matrix dimensions.
        atlas_name: Name of the atlas used (e.g., 'AAL', 'Schaefer').
        transformed: Boolean indicating if Fisher Z-transform has been applied.
    """
    subject_id: str
    matrix: np.ndarray
    roi_labels: List[str]
    atlas_name: str
    transformed: bool = False

    def __post_init__(self):
        """Validate the connectivity matrix instance."""
        self._validate()

    def _validate(self) -> None:
        """Validates the matrix structure and consistency."""
        if not isinstance(self.matrix, np.ndarray):
            raise ValidationError("Matrix must be a numpy array.")
        
        if self.matrix.ndim != 2:
            raise ValidationError(f"Matrix must be 2D, got {self.matrix.ndim}D.")
        
        if self.matrix.shape[0] != self.matrix.shape[1]:
            raise ValidationError(f"Matrix must be square, got shape {self.matrix.shape}.")
        
        if len(self.roi_labels) != self.matrix.shape[0]:
            raise ValidationError(f"ROI labels count ({len(self.roi_labels)}) must match matrix dimension ({self.matrix.shape[0]}).")
        
        if not isinstance(self.subject_id, str) or not self.subject_id:
            raise ValidationError("subject_id must be a non-empty string.")

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the ConnectivityMatrix to a dictionary.
        Note: The matrix is converted to a list of lists for JSON serialization if needed.
        """
        return {
            'subject_id': self.subject_id,
            'matrix': self.matrix.tolist(),
            'roi_labels': self.roi_labels,
            'atlas_name': self.atlas_name,
            'transformed': self.transformed
        }

def create_subject_from_dict(data: Dict[str, Any]) -> Subject:
    """
    Factory function to create a Subject from a dictionary.
    Validates the input data against the Subject schema requirements.
    """
    required_keys = ['subject_id', 'group', 'years_of_training', 'age', 'sex', 'motion_score', 'ses_score']
    missing_keys = [k for k in required_keys if k not in data]
    
    if missing_keys:
        raise ValidationError(f"Missing required keys for Subject: {missing_keys}")
    
    # Ensure types are correct (basic coercion)
    try:
        return Subject(
            subject_id=str(data['subject_id']),
            group=str(data['group']),
            years_of_training=float(data['years_of_training']),
            age=float(data['age']),
            sex=str(data['sex']),
            motion_score=float(data['motion_score']),
            ses_score=float(data['ses_score'])
        )
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Type coercion failed for Subject: {e}")

def create_subjects_from_dataframe(df: pd.DataFrame) -> List[Subject]:
    """
    Factory function to create a list of Subject instances from a pandas DataFrame.
    
    Args:
        df: DataFrame with columns matching Subject attributes.
        
    Returns:
        List of validated Subject objects.
        
    Raises:
        ValidationError: If any row fails validation.
    """
    import pandas as pd
    
    required_columns = ['subject_id', 'group', 'years_of_training', 'age', 'sex', 'motion_score', 'ses_score']
    missing_columns = [c for c in required_columns if c not in df.columns]
    
    if missing_columns:
        raise ValidationError(f"DataFrame missing required columns: {missing_columns}")
    
    subjects = []
    for idx, row in df.iterrows():
        try:
            subject_data = row.to_dict()
            # Handle potential NaN values if necessary, though validation might catch them
            subject = create_subject_from_dict(subject_data)
            subjects.append(subject)
        except ValidationError as e:
            raise ValidationError(f"Validation failed for row {idx}: {e}")
    
    return subjects
