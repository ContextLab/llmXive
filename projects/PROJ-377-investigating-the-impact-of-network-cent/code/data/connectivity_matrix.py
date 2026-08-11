"""
Data model for a functional connectivity matrix.

Encapsulates connectivity data derived from fMRI time-series for a specific subject.
"""
import numpy as np
from typing import Optional, List, Tuple
import os
from pathlib import Path


class ConnectivityMatrix:
    """
    Represents a functional connectivity matrix for a subject.

    Attributes:
        subject_id (str): Unique identifier of the subject.
        matrix (np.ndarray): 2D numpy array of connectivity values (N_nodes x N_nodes).
        atlas_name (str): Name of the atlas used (e.g., 'AAL3').
        node_names (List[str]): Optional list of region names corresponding to matrix indices.
        file_path (Optional[Path]): Path where the matrix is saved on disk.
    """
    def __init__(
        self,
        subject_id: str,
        matrix: np.ndarray,
        atlas_name: str = "AAL3",
        node_names: Optional[List[str]] = None,
        file_path: Optional[Path] = None
    ):
        """
        Initialize a ConnectivityMatrix.

        Args:
            subject_id: Unique subject identifier.
            matrix: 2D numpy array of connectivity values.
            atlas_name: Name of the parcellation atlas.
            node_names: List of region names.
            file_path: Path to save/load the matrix.
        """
        self.subject_id = subject_id
        self.atlas_name = atlas_name
        self.node_names = node_names
        self.file_path = file_path

        # Validate and store matrix
        if not isinstance(matrix, np.ndarray):
            raise TypeError("Matrix must be a numpy array")
        if matrix.ndim != 2:
            raise ValueError("Matrix must be 2D")
        if matrix.shape[0] != matrix.shape[1]:
            raise ValueError("Matrix must be square")

        self.matrix = matrix.astype(np.float32)  # Memory efficient storage

    @property
    def shape(self) -> Tuple[int, int]:
        """Return the shape of the matrix."""
        return self.matrix.shape

    @property
    def n_nodes(self) -> int:
        """Return the number of nodes in the graph."""
        return self.matrix.shape[0]

    def save(self, path: Optional[Path] = None) -> None:
        """
        Save the connectivity matrix to disk.

        Args:
            path: Destination path. If None, uses self.file_path.
        """
        save_path = path or self.file_path
        if save_path is None:
            raise ValueError("No file path provided to save the matrix")

        # Ensure directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)

        np.save(str(save_path), self.matrix)
        self.file_path = save_path

    @classmethod
    def load(cls, file_path: Path, subject_id: str, atlas_name: str = "AAL3") -> 'ConnectivityMatrix':
        """
        Load a connectivity matrix from disk.

        Args:
            file_path: Path to the .npy file.
            subject_id: Subject ID to associate with the matrix.
            atlas_name: Atlas name associated with the matrix.

        Returns:
            ConnectivityMatrix instance.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Connectivity matrix file not found: {file_path}")

        matrix = np.load(str(file_path))
        return cls(
            subject_id=subject_id,
            matrix=matrix,
            atlas_name=atlas_name,
            file_path=file_path
        )

    def to_sparse_dict(self) -> dict:
        """
        Convert the matrix to a sparse dictionary representation (for specific analyses).
        Only includes non-zero values.
        """
        sparse_data = {}
        indices = np.argwhere(self.matrix != 0)
        for i, j in indices:
            sparse_data[f"{i}_{j}"] = float(self.matrix[i, j])
        return sparse_data
