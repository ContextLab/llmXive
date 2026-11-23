"""
Connectivity matrix data model.

Represents the functional connectivity matrix derived from fMRI time series.
"""
from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class ConnectivityMatrix:
    """
    Represents a functional connectivity matrix.
    
    Attributes:
        subject_id: ID of the subject this matrix belongs to
        matrix: 2D numpy array of correlation values (N x N)
        roi_labels: List of ROI names/labels corresponding to matrix rows/cols
        parcellation: Name of the parcellation scheme used (e.g., 'Schaefer200')
        threshold: Optional threshold applied to the matrix
        is_sparse: Whether the matrix has been thresholded to be sparse
    """
    subject_id: str
    matrix: np.ndarray
    roi_labels: Optional[list] = None
    parcellation: str = "Schaefer200"
    threshold: Optional[float] = None
    is_sparse: bool = False

    def __post_init__(self) -> None:
        """Validate matrix dimensions and values."""
        if self.matrix.ndim != 2:
            raise ValueError(f"Matrix must be 2D, got {self.matrix.ndim}D")
        
        if self.matrix.shape[0] != self.matrix.shape[1]:
            raise ValueError("Matrix must be square")
        
        # Validate correlation values are in [-1, 1]
        if np.any(self.matrix < -1.0) or np.any(self.matrix > 1.0):
            # Allow slight floating point errors
            if np.any(self.matrix < -1.001) or np.any(self.matrix > 1.001):
                raise ValueError("Correlation values must be in [-1, 1]")

    @property
    def n_rois(self) -> int:
        """Return number of ROIs (matrix dimension)."""
        return self.matrix.shape[0]

    def to_array(self) -> np.ndarray:
        """Return the matrix as a numpy array."""
        return self.matrix.copy()

    def set_threshold(self, threshold: float) -> None:
        """Apply threshold to the matrix (in-place)."""
        if self.threshold is not None:
            # Reset previous threshold
            pass  # In practice, we'd store the original or recompute
        
        self.matrix[np.abs(self.matrix) < threshold] = 0.0
        self.threshold = threshold
        self.is_sparse = True

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "subject_id": self.subject_id,
            "matrix": self.matrix.tolist(),
            "roi_labels": self.roi_labels,
            "parcellation": self.parcellation,
            "threshold": self.threshold,
            "is_sparse": self.is_sparse,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConnectivityMatrix":
        """Create from dictionary."""
        return cls(
            subject_id=data["subject_id"],
            matrix=np.array(data["matrix"]),
            roi_labels=data.get("roi_labels"),
            parcellation=data.get("parcellation", "Schaefer200"),
            threshold=data.get("threshold"),
            is_sparse=data.get("is_sparse", False),
        )
