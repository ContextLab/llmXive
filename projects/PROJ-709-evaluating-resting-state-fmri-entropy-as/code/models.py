from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
import numpy as np

@dataclass
class Subject:
    """
    Represents a single research participant in the fMRI study.
    
    Attributes:
        subject_id: Unique identifier for the subject (e.g., 'sub-001').
        nii_path: Path to the preprocessed NIfTI file containing fMRI time series.
        phenotypic_data: Dictionary containing phenotypic/clinical data 
                         (e.g., ADHD-RS score, age, sex, diagnosis label).
        atlas_mask_path: Optional path to the atlas mask file defining parcels.
        time_series: Optional numpy array of shape (time_points, parcels) loaded from nii_path.
    """
    subject_id: str
    nii_path: Path
    phenotypic_data: Dict[str, Any]
    atlas_mask_path: Optional[Path] = None
    time_series: Optional[np.ndarray] = None

    def load_time_series(self) -> np.ndarray:
        """
        Loads the fMRI time series from the NIfTI file using nibabel.
        Returns a numpy array of shape (time_points, parcels).
        Raises FileNotFoundError if the path does not exist.
        """
        import nibabel as nib
        if self.time_series is not None:
            return self.time_series
        
        if not self.nii_path.exists():
            raise FileNotFoundError(f"NIfTI file not found: {self.nii_path}")
        
        img = nib.load(str(self.nii_path))
        data = img.get_fdata()
        
        # Handle potential 4D data (x, y, z, time) -> reshape to (time, voxels) or (time, parcels)
        # Assuming preprocessing has already parcellated or we are loading raw volumes.
        # If raw, we assume the downstream entropy engine handles the mapping.
        # For this model, we store the raw or pre-parcellated data.
        if len(data.shape) == 4:
            # Reshape to (time, -1)
            self.time_series = data.reshape(-1, data.shape[-1]).T # (time, voxels)
        elif len(data.shape) == 3:
            # Static map? Unlikely for fMRI, but handle as (1, voxels)
            self.time_series = data.flatten().reshape(1, -1).T
        else:
            self.time_series = data
            
        return self.time_series

@dataclass
class Parcel:
    """
    Represents a specific brain region (parcel) defined by an atlas.
    
    Attributes:
        index: The integer index of this parcel in the atlas mask.
        mask: A boolean numpy array (same shape as fMRI volume) where True indicates
              voxels belonging to this parcel.
        label: Optional descriptive name (e.g., 'Frontal_Pole').
    """
    index: int
    mask: np.ndarray
    label: Optional[str] = None

    def extract_mean_signal(self, volume_data: np.ndarray) -> float:
        """
        Extracts the mean signal intensity for this parcel from a 3D volume.
        
        Args:
            volume_data: 3D numpy array representing a single time point.
            
        Returns:
            Mean signal value of the voxels in the parcel.
        """
        if self.mask.shape != volume_data.shape:
            raise ValueError(f"Mask shape {self.mask.shape} does not match volume shape {volume_data.shape}")
        
        parcel_voxels = volume_data[self.mask]
        if parcel_voxels.size == 0:
            return 0.0
        return float(np.mean(parcel_voxels))

@dataclass
class EntropyFeature:
    """
    Represents a calculated entropy feature for a specific subject and parcel.
    
    Attributes:
        subject_id: ID of the subject.
        parcel_index: Index of the parcel.
        parcel_label: Name of the parcel (optional).
        entropy_value: The calculated Sample Entropy value.
        parameters: Dictionary of parameters used for calculation (e.g., m, r).
        metadata: Additional metadata (e.g., number of time points used, SD of signal).
    """
    subject_id: str
    parcel_index: int
    entropy_value: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    parcel_label: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the feature to a dictionary suitable for CSV serialization.
        """
        return {
            "subject_id": self.subject_id,
            "parcel_index": self.parcel_index,
            "parcel_label": self.parcel_label or f"parcel_{self.parcel_index}",
            "entropy_value": self.entropy_value,
            **self.parameters,
            **self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntropyFeature":
        """
        Constructs an EntropyFeature from a dictionary.
        """
        return cls(
            subject_id=data["subject_id"],
            parcel_index=data["parcel_index"],
            parcel_label=data.get("parcel_label"),
            entropy_value=data["entropy_value"],
            parameters={k: v for k, v in data.items() if k not in cls._standard_fields()},
            metadata={k: v for k, v in data.items() if k not in cls._standard_fields()},
        )

    @staticmethod
    def _standard_fields() -> set:
        return {"subject_id", "parcel_index", "parcel_label", "entropy_value"}