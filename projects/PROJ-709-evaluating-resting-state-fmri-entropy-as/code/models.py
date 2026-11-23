"""
Base data structures for the fMRI entropy analysis pipeline.

Defines core dataclasses: Subject, Parcel, and EntropyFeature.
These structures are used throughout the pipeline to represent
subjects, brain parcels, and computed entropy features.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
import numpy as np


@dataclass
class Subject:
    """
    Represents a single subject in the study.

    Attributes:
        subject_id: Unique identifier for the subject (e.g., 'sub-001').
        nifti_path: Path to the preprocessed NIfTI file for this subject.
        phenotypic_data: Dictionary containing phenotypic data (e.g., ADHD-RS score, age, sex).
        time_points: Number of time points in the fMRI time series (after scrubbing/truncation).
        mean_fd: Mean Framewise Displacement for this subject (optional).
        scrub_fraction: Fraction of volumes scrubbed (optional).
    """
    subject_id: str
    nifti_path: Path
    phenotypic_data: Dict[str, Any] = field(default_factory=dict)
    time_points: Optional[int] = None
    mean_fd: Optional[float] = None
    scrub_fraction: Optional[float] = None

    @property
    def adhd_rs_score(self) -> Optional[float]:
        """Retrieve ADHD-RS score if available."""
        return self.phenotypic_data.get('adhd_rs_score')

    @property
    def diagnosis(self) -> Optional[str]:
        """Retrieve binary diagnosis if available."""
        return self.phenotypic_data.get('diagnosis')


@dataclass
class Parcel:
    """
    Represents a brain parcel (region of interest) in the atlas.

    Attributes:
        index: Integer index of the parcel in the atlas (0 to N-1).
        mask: Boolean numpy array representing the parcel mask in 3D space.
        name: Optional name or label for the parcel.
        atlas_name: Name of the atlas used (e.g., 'Schaefer200').
    """
    index: int
    mask: np.ndarray
    name: Optional[str] = None
    atlas_name: str = "Schaefer200"

    def __post_init__(self):
        """Validate that mask is a boolean numpy array."""
        if not isinstance(self.mask, np.ndarray):
            raise TypeError(f"mask must be a numpy.ndarray, got {type(self.mask)}")
        if self.mask.dtype != bool:
            raise TypeError(f"mask must be of boolean dtype, got {self.mask.dtype}")


@dataclass
class EntropyFeature:
    """
    Represents a computed entropy feature for a specific subject and parcel.

    Attributes:
        subject_id: ID of the subject.
        parcel_index: Index of the parcel.
        parcel_name: Name of the parcel (optional).
        entropy_value: The computed Sample Entropy value.
        method: Entropy calculation method (e.g., 'SampEn').
        parameters: Dictionary of parameters used (e.g., m, r).
        timestamp: Optional timestamp of computation.
    """
    subject_id: str
    parcel_index: int
    entropy_value: float
    method: str = "SampEn"
    parameters: Dict[str, Any] = field(default_factory=lambda: {"m": 2, "r": 0.2})
    parcel_name: Optional[str] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the feature to a dictionary for serialization."""
        return {
            "subject_id": self.subject_id,
            "parcel_index": self.parcel_index,
            "parcel_name": self.parcel_name,
            "entropy_value": self.entropy_value,
            "method": self.method,
            "parameters": self.parameters,
            "timestamp": self.timestamp
        }