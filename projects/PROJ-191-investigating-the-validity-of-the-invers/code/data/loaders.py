"""
Data loading and harmonization utilities for the Inverse-Square Law investigation.

This module defines the base data model `HarmonizedDataset` used to store
aligned force-vs-separation data from multiple experiments, along with
their associated uncertainties and covariance structures.
"""

from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import pandas as pd
from pathlib import Path


@dataclass
class HarmonizedDataset:
    """
    A unified container for harmonized experimental data from multiple sources.

    This dataset aligns force measurements from different experiments onto a
    common separation grid, converts all units to SI (Newtons, meters), and
    constructs a full covariance matrix accounting for statistical and
    systematic uncertainties.

    Attributes:
        separation (np.ndarray): 1D array of separation distances in meters (m).
        force (np.ndarray): 1D array of measured forces in Newtons (N).
        covariance (np.ndarray): 2D array representing the full covariance matrix
            of the force measurements (N^2).
        source_ids (list[str]): List of identifiers for the source experiments
            contributing to this dataset.
        metadata (dict): Additional metadata regarding the harmonization process,
            such as the common grid resolution, interpolation method, or
            specific version of the harmonization algorithm used.
    """

    separation: np.ndarray
    force: np.ndarray
    covariance: np.ndarray
    source_ids: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate the integrity of the dataset upon initialization."""
        # Ensure inputs are numpy arrays
        if not isinstance(self.separation, np.ndarray):
            self.separation = np.asarray(self.separation, dtype=np.float64)
        if not isinstance(self.force, np.ndarray):
            self.force = np.asarray(self.force, dtype=np.float64)
        if not isinstance(self.covariance, np.ndarray):
            self.covariance = np.asarray(self.covariance, dtype=np.float64)

        # Validate dimensions
        n_points = len(self.separation)
        if len(self.force) != n_points:
            raise ValueError(
                f"Length mismatch: separation has {n_points} points, "
                f"but force has {len(self.force)} points."
            )
        if self.covariance.shape != (n_points, n_points):
            raise ValueError(
                f"Covariance matrix shape {self.covariance.shape} does not match "
                f"data length {n_points}."
            )

        # Validate data types
        if self.separation.dtype not in [np.float64, np.float32]:
            raise ValueError("Separation array must be of float type.")
        if self.force.dtype not in [np.float64, np.float32]:
            raise ValueError("Force array must be of float type.")

        # Validate physical constraints
        if np.any(self.separation <= 0):
            raise ValueError("Separation distances must be strictly positive.")

        # Validate covariance matrix properties
        if not np.allclose(self.covariance, self.covariance.T, atol=1e-12):
            raise ValueError("Covariance matrix must be symmetric.")
        
        # Check for positive semi-definiteness (eigenvalues >= 0)
        # Using a small tolerance for numerical noise
        eigvals = np.linalg.eigvalsh(self.covariance)
        if np.any(eigvals < -1e-12):
            raise ValueError(
                "Covariance matrix is not positive semi-definite. "
                f"Min eigenvalue: {np.min(eigvals)}"
            )

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the dataset to a pandas DataFrame.

        Returns:
            pd.DataFrame: A DataFrame with columns 'separation_m', 'force_N',
                and columns for the lower triangle of the covariance matrix
                (optional, usually large). For standard analysis, returns
                a simple table of separation and force.
        """
        df = pd.DataFrame({
            'separation_m': self.separation,
            'force_N': self.force
        })
        # Add source metadata as columns if available
        if self.source_ids:
            df['source_id'] = self.source_ids[0] if len(self.source_ids) == 1 else 'mixed'
        
        return df

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, covariance: np.ndarray) -> "HarmonizedDataset":
        """
        Create a HarmonizedDataset from a pandas DataFrame and a covariance matrix.

        Args:
            df: DataFrame containing at least 'separation_m' and 'force_N' columns.
            covariance: 2D numpy array of the covariance matrix.

        Returns:
            HarmonizedDataset: Initialized instance.
        """
        return cls(
            separation=df['separation_m'].values,
            force=df['force_N'].values,
            covariance=covariance,
            source_ids=[df['source_id'].iloc[0]] if 'source_id' in df.columns else []
        )

    def save_to_csv(self, path: Path) -> None:
        """
        Save the primary data (separation and force) to a CSV file.
        
        Note: The full covariance matrix is typically too large for standard CSV
        representation and should be saved separately (e.g., as .npy or .h5).

        Args:
            path: File path to save the CSV.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.to_dataframe().to_csv(path, index=False)

    def save_covariance(self, path: Path) -> None:
        """
        Save the covariance matrix to a NumPy .npy file.

        Args:
            path: File path to save the .npy file.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(path, self.covariance)

    @classmethod
    def load_from_csv(cls, csv_path: Path, cov_path: Path, metadata: Optional[dict] = None) -> "HarmonizedDataset":
        """
        Load a HarmonizedDataset from a CSV file and a corresponding covariance file.

        Args:
            csv_path: Path to the CSV file containing separation and force.
            cov_path: Path to the .npy file containing the covariance matrix.
            metadata: Optional dictionary of metadata to attach to the dataset.

        Returns:
            HarmonizedDataset: Loaded instance.
        """
        df = pd.read_csv(csv_path)
        covariance = np.load(cov_path)
        instance = cls.from_dataframe(df, covariance)
        if metadata:
            instance.metadata.update(metadata)
        return instance

    def get_statistics(self) -> dict:
        """
        Compute basic statistics for the dataset.

        Returns:
            dict: Dictionary containing min/max separation, mean force, 
                and covariance trace/determinant.
        """
        return {
            "n_points": len(self.separation),
            "separation_min_m": float(np.min(self.separation)),
            "separation_max_m": float(np.max(self.separation)),
            "force_mean_N": float(np.mean(self.force)),
            "force_std_N": float(np.std(self.force)),
            "covariance_trace": float(np.trace(self.covariance)),
            "covariance_rank": int(np.linalg.matrix_rank(self.covariance))
        }