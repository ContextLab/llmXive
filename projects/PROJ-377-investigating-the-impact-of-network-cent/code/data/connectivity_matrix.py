"""
Data model for a functional connectivity matrix.
"""
import numpy as np
from typing import Optional, List, Tuple
import os
from pathlib import Path

class ConnectivityMatrix:
    """
    Represents a functional connectivity matrix for a subject.
    
    Attributes:
        matrix: 2D numpy array representing the connectivity matrix.
        region_names: List of region names corresponding to matrix rows/cols.
        subject_id: ID of the subject this matrix belongs to.
        method: Method used to calculate connectivity (e.g., 'pearson', 'spearman').
    """
    def __init__(
        self,
        matrix: np.ndarray,
        region_names: Optional[List[str]] = None,
        subject_id: Optional[str] = None,
        method: str = 'pearson'
    ):
        """
        Initialize a ConnectivityMatrix.
        
        Args:
            matrix: 2D numpy array of connectivity values.
            region_names: Optional list of region names.
            subject_id: Optional subject identifier.
            method: Correlation method used.
        """
        if not isinstance(matrix, np.ndarray):
            raise TypeError("matrix must be a numpy array")
        if matrix.ndim != 2:
            raise ValueError("matrix must be 2D")
        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError("matrix must be square")
        
        self.matrix = matrix
        self.region_names = region_names
        self.subject_id = subject_id
        self.method = method

    @property
    def shape(self) -> Tuple[int, int]:
        """Return the shape of the matrix."""
        return self.matrix.shape

    @property
    def n_regions(self) -> int:
        """Return the number of regions."""
        return self.matrix.shape[0]

    def to_array(self) -> np.ndarray:
        """Return the underlying numpy array."""
        return self.matrix.copy()

    def save(self, path: Path) -> None:
        """
        Save the connectivity matrix to a file.
        
        Args:
            path: Path to save the matrix (supports .npy or .csv).
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if path.suffix == '.npy':
            np.save(path, self.matrix)
        elif path.suffix == '.csv':
            import pandas as pd
            df = pd.DataFrame(self.matrix, columns=self.region_names if self.region_names else None)
            df.to_csv(path, index=False)
        else:
            raise ValueError(f"Unsupported file extension: {path.suffix}")

    @classmethod
    def load(cls, path: Path, subject_id: Optional[str] = None) -> 'ConnectivityMatrix':
        """
        Load a connectivity matrix from a file.
        
        Args:
            path: Path to the matrix file.
            subject_id: Optional subject ID to associate with the matrix.
        
        Returns:
            A ConnectivityMatrix instance.
        """
        path = Path(path)
        
        if path.suffix == '.npy':
            matrix = np.load(path)
        elif path.suffix == '.csv':
            import pandas as pd
            df = pd.read_csv(path)
            matrix = df.to_numpy()
            region_names = df.columns.tolist()
        else:
            raise ValueError(f"Unsupported file extension: {path.suffix}")
        
        return cls(matrix=matrix, region_names=region_names if path.suffix == '.csv' else None, subject_id=subject_id)