"""
Data models for the Brain Network Dynamics and Musical Creativity project.

This module defines the core data structures for subjects and their
associated behavioral scores, aligned with the project's data model.
"""
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class Subject:
    """
    Represents a study participant.

    Attributes:
        id: Unique subject identifier (e.g., 'sub-001').
        age: Age of the subject in years.
        gender: Gender of the subject (e.g., 'M', 'F', 'Other').
        raw_fMRI_path: Path to the raw fMRI NIfTI file.
        preprocessed_fMRI_path: Path to the preprocessed fMRI NIfTI file.
        behavioral_path: Path to the subject's behavioral data file.
    """
    id: str
    age: Optional[int] = None
    gender: Optional[str] = None
    raw_fMRI_path: Optional[str] = None
    preprocessed_fMRI_path: Optional[str] = None
    behavioral_path: Optional[str] = None

    def __post_init__(self):
        """Validate that an ID is present."""
        if not self.id:
            raise ValueError("Subject ID cannot be empty.")


@dataclass
class BehavioralScore:
    """
    Represents a behavioral metric associated with a subject.

    Attributes:
        subject_id: The ID of the subject this score belongs to.
        score_value: The numeric value of the score (e.g., Fluid Intelligence score).
        source_type: The type of metric (e.g., 'fluid_intelligence', 'creativity_score').
        source_file: The file path where this score was originally recorded.
        metadata: Optional dictionary for additional context.
    """
    subject_id: str
    score_value: float
    source_type: str
    source_file: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate core attributes."""
        if not self.subject_id:
            raise ValueError("Subject ID cannot be empty.")
        if self.score_value is None:
            raise ValueError("Score value cannot be None.")
        if not self.source_type:
            raise ValueError("Source type cannot be empty.")
