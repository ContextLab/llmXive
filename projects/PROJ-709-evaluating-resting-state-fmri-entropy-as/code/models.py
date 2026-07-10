"""
Core data structures for the fMRI entropy analysis pipeline.

Defines the fundamental data classes used throughout the project:
- Subject: Represents a single participant with their data paths and phenotypic traits.
- Parcel: Represents a brain region (ROI) defined by an atlas index and mask.
- EntropyFeature: Represents the computed entropy value for a specific subject-parcel pair.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
import numpy as np


@dataclass
class Subject:
    """
    Represents a single study participant.

    Attributes:
        subject_id (str): Unique identifier for the subject (e.g., 'sub-01').
        nifti_path (Path): Path to the preprocessed NIfTI file (e.g., scrubbed/truncated).
        phenotypic_data (Dict[str, Any]): Dictionary containing phenotypic information
            (e.g., ADHD status, age, sex, motion metrics).
        runs (List[str]): List of run identifiers associated with this subject.
    """
    subject_id: str
    nifti_path: Path
    phenotypic_data: Dict[str, Any] = field(default_factory=dict)
    runs: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate that the NIfTI path exists."""
        if not self.nifti_path.exists():
            raise FileNotFoundError(f"NIfTI file not found for subject {self.subject_id}: {self.nifti_path}")

    @property
    def adhd_status(self) -> Optional[int]:
        """Convenience accessor for ADHD diagnosis (1=ADHD, 0=Control)."""
        return self.phenotypic_data.get('adhd_status')

    @property
    def age(self) -> Optional[float]:
        """Convenience accessor for age."""
        return self.phenotypic_data.get('age')

    @property
    def sex(self) -> Optional[str]:
        """Convenience accessor for sex."""
        return self.phenotypic_data.get('sex')


@dataclass
class Parcel:
    """
    Represents a single brain parcel (ROI) from an atlas.

    Attributes:
        index (int): 0-based index of the parcel in the atlas.
        name (str): Human-readable name of the parcel (e.g., 'Frontal_Superior_Left').
        mask (np.ndarray): Binary 3D or 4D mask array for this parcel.
        atlas_name (str): Name of the atlas used (e.g., 'Schaefer200').
    """
    index: int
    name: str
    mask: np.ndarray
    atlas_name: str = "Default"

    def __post_init__(self):
        """Ensure mask is a numpy array."""
        if not isinstance(self.mask, np.ndarray):
            self.mask = np.array(self.mask)

    @property
    def volume(self) -> int:
        """Return the number of voxels in the parcel."""
        return int(np.sum(self.mask > 0))


@dataclass
class EntropyFeature:
    """
    Represents a computed entropy value for a specific subject and parcel.

    Attributes:
        subject_id (str): ID of the subject.
        parcel_index (int): Index of the parcel.
        parcel_name (str): Name of the parcel.
        entropy_value (float): The computed Sample Entropy value.
        method (str): Method used (e.g., 'SampEn').
        parameters (Dict[str, Any]): Parameters used for calculation (e.g., m, r).
    """
    subject_id: str
    parcel_index: int
    parcel_name: str
    entropy_value: float
    method: str = "SampEn"
    parameters: Dict[str, Any] = field(default_factory=lambda: {"m": 2, "r": 0.2})

    def to_dict(self) -> Dict[str, Any]:
        """Convert the feature to a dictionary for serialization."""
        return {
            "subject_id": self.subject_id,
            "parcel_index": self.parcel_index,
            "parcel_name": self.parcel_name,
            "entropy_value": self.entropy_value,
            "method": self.method,
            "parameters": self.parameters
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EntropyFeature':
        """Create an EntropyFeature from a dictionary."""
        return cls(
            subject_id=data["subject_id"],
            parcel_index=data["parcel_index"],
            parcel_name=data["parcel_name"],
            entropy_value=data["entropy_value"],
            method=data.get("method", "SampEn"),
            parameters=data.get("parameters", {"m": 2, "r": 0.2})
        )