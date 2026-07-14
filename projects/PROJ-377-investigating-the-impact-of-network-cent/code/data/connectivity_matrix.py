"""
ConnectivityMatrix data model.

Represents a functional connectivity matrix for a subject,
including the matrix data, region labels, and metadata.
"""

import numpy as np
from typing import Optional, List, Tuple
import os
from pathlib import Path

class ConnectivityMatrix:
    """
    Functional connectivity matrix for a subject.
    
    Attributes:
        subject_id: Associated subject identifier
        matrix: 2D numpy array of connectivity values (n_regions x n_regions)
        region_labels: List of region names corresponding to matrix indices
        atlas_name: Name of the atlas used (e.g., 'AAL3')
        matrix_type: Type of connectivity (e.g., 'correlation', 'partial')
        path: Path to saved matrix file
    """
    
    def __init__(
        self,
        subject_id: str,
        matrix: np.ndarray,
        region_labels: List[str],
        atlas_name: str = "AAL3",
        matrix_type: str = "correlation",
        path: Optional[Path] = None
    ):
        """
        Initialize a ConnectivityMatrix.
        
        Args:
            subject_id: Unique subject identifier
            matrix: 2D connectivity matrix (n x n)
            region_labels: List of region names
            atlas_name: Name of the atlas used
            matrix_type: Type of connectivity measure
            path: Optional path where matrix is saved
        
        Raises:
            ValueError: If matrix dimensions don't match region labels
        """
        self.subject_id = subject_id
        self.atlas_name = atlas_name
        self.matrix_type = matrix_type
        self.path = Path(path) if path else None
        
        # Validate and set matrix
        if not isinstance(matrix, np.ndarray):
            matrix = np.array(matrix)
        
        if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
            raise ValueError("Matrix must be 2D and square")
        
        if len(region_labels) != matrix.shape[0]:
            raise ValueError(
                f"Number of region labels ({len(region_labels)}) must match "
                f"matrix dimension ({matrix.shape[0]})"
            )
        
        self.matrix = matrix.astype(np.float32)
        self.region_labels = region_labels
    
    @property
    def n_regions(self) -> int:
        """Number of brain regions in the matrix."""
        return self.matrix.shape[0]
    
    @property
    def is_symmetric(self) -> bool:
        """Check if matrix is symmetric."""
        return np.allclose(self.matrix, self.matrix.T)
    
    def get_upper_triangular(self) -> np.ndarray:
        """
        Extract upper triangular part of the matrix (excluding diagonal).
        
        Returns:
            1D array of upper triangular values
        """
        return self.matrix[np.triu_indices(self.n_regions, k=1)]
    
    def get_region_connectivity(self, region_idx: int) -> np.ndarray:
        """
        Get connectivity values for a specific region.
        
        Args:
            region_idx: Index of the region
        
        Returns:
            1D array of connectivity values for that region
        """
        if not 0 <= region_idx < self.n_regions:
            raise IndexError(f"Region index {region_idx} out of bounds")
        
        return self.matrix[region_idx, :]
    
    def get_region_pair_connectivity(self, idx1: int, idx2: int) -> float:
        """
        Get connectivity between two specific regions.
        
        Args:
            idx1: Index of first region
            idx2: Index of second region
        
        Returns:
            Connectivity value between the two regions
        """
        return float(self.matrix[idx1, idx2])
    
    def save(self, path: Optional[Path] = None) -> Path:
        """
        Save connectivity matrix to disk.
        
        Args:
            path: Optional path to save to. If None, uses self.path.
        
        Returns:
            Path where matrix was saved
        
        Raises:
            ValueError: If no path is provided
        """
        save_path = Path(path) if path else self.path
        
        if save_path is None:
            raise ValueError("No save path provided")
        
        # Ensure directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save matrix and metadata
        np.savez_compressed(
            save_path,
            matrix=self.matrix,
            region_labels=np.array(self.region_labels),
            atlas_name=self.atlas_name,
            matrix_type=self.matrix_type,
            subject_id=self.subject_id
        )
        
        self.path = save_path
        return save_path
    
    @classmethod
    def load(cls, path: Path) -> 'ConnectivityMatrix':
        """
        Load a connectivity matrix from disk.
        
        Args:
            path: Path to the saved .npz file
        
        Returns:
            ConnectivityMatrix instance
        """
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Matrix file not found: {path}")
        
        data = np.load(path, allow_pickle=True)
        
        matrix = data['matrix']
        region_labels = list(data['region_labels'])
        atlas_name = str(data['atlas_name'])
        matrix_type = str(data['matrix_type'])
        subject_id = str(data['subject_id'])
        
        return cls(
            subject_id=subject_id,
            matrix=matrix,
            region_labels=region_labels,
            atlas_name=atlas_name,
            matrix_type=matrix_type,
            path=path
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            'subject_id': self.subject_id,
            'atlas_name': self.atlas_name,
            'matrix_type': self.matrix_type,
            'n_regions': self.n_regions,
            'region_labels': self.region_labels,
            'path': str(self.path) if self.path else None
        }
    
    def __repr__(self) -> str:
        return (
            f"ConnectivityMatrix(subject_id='{self.subject_id}', "
            f"n_regions={self.n_regions}, atlas='{self.atlas_name}')"
        )
