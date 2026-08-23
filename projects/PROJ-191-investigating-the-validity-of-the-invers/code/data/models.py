"""
Data models for the HarmonizedDataset.

This module defines the core data structures used to represent the harmonized
experimental data from multiple sources, aligned on a common grid.
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import numpy as np
import pandas as pd
from pathlib import Path
import json
import logging
from config import get_logger

logger = get_logger(__name__)

@dataclass
class HarmonizedDataset:
    """
    A unified data structure for harmonized experimental force vs. separation data.
    
    Attributes:
        separation_m: 1D numpy array of separation distances in meters (SI units).
        force_N: 1D numpy array of force measurements in Newtons (SI units).
        covariance_matrix: 2D numpy array representing the full or block-diagonal
                           covariance matrix of the force measurements.
        metadata: Dictionary containing provenance and processing information.
        source_runs: List of dictionaries, each representing a source experiment run
                     with its original properties.
    """
    separation_m: np.ndarray
    force_N: np.ndarray
    covariance_matrix: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_runs: list = field(default_factory=list)

    def __post_init__(self):
        """Validate dimensions and types after initialization."""
        if not isinstance(self.separation_m, np.ndarray):
            raise TypeError("separation_m must be a numpy array")
        if not isinstance(self.force_N, np.ndarray):
            raise TypeError("force_N must be a numpy array")
        if not isinstance(self.covariance_matrix, np.ndarray):
            raise TypeError("covariance_matrix must be a numpy array")
        
        if len(self.separation_m) != len(self.force_N):
            raise ValueError(
                f"separation_m and force_N must have the same length. "
                f"Got {len(self.separation_m)} and {len(self.force_N)}."
            )
        
        n_points = len(self.separation_m)
        if self.covariance_matrix.shape != (n_points, n_points):
            raise ValueError(
                f"covariance_matrix shape {self.covariance_matrix.shape} "
                f"does not match data length {n_points}."
            )

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the dataset to a pandas DataFrame for analysis.
        
        Returns:
            pd.DataFrame: A DataFrame with columns for separation, force, 
                          and diagonal uncertainties.
        """
        std_dev = np.sqrt(np.diag(self.covariance_matrix))
        return pd.DataFrame({
            'separation_m': self.separation_m,
            'force_N': self.force_N,
            'uncertainty_N': std_dev
        })

    def save(self, output_path: Path) -> None:
        """
        Save the dataset to disk in a serialized format (Numpy .npz).
        
        Args:
            output_path: Path to the output file.
        """
        if not output_path.parent.exists():
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save numpy arrays
        np.savez(
            output_path,
            separation_m=self.separation_m,
            force_N=self.force_N,
            covariance_matrix=self.covariance_matrix,
            metadata=json.dumps(self.metadata),
            source_runs=json.dumps(self.source_runs)
        )
        logger.info(f"Saved HarmonizedDataset to {output_path}")

    @classmethod
    def load(cls, input_path: Path) -> 'HarmonizedDataset':
        """
        Load a HarmonizedDataset from a .npz file.
        
        Args:
            input_path: Path to the input file.
            
        Returns:
            HarmonizedDataset: The loaded dataset.
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {input_path}")
        
        data = np.load(input_path, allow_pickle=True)
        
        metadata = json.loads(str(data['metadata']))
        source_runs = json.loads(str(data['source_runs']))
        
        return cls(
            separation_m=data['separation_m'],
            force_N=data['force_N'],
            covariance_matrix=data['covariance_matrix'],
            metadata=metadata,
            source_runs=source_runs
        )

    def get_statistics(self) -> Dict[str, float]:
        """
        Calculate basic statistics for the dataset.
        
        Returns:
            Dictionary containing min, max, mean of separation and force.
        """
        return {
            'separation_min_m': float(np.min(self.separation_m)),
            'separation_max_m': float(np.max(self.separation_m)),
            'force_min_N': float(np.min(self.force_N)),
            'force_max_N': float(np.max(self.force_N)),
            'n_points': int(len(self.separation_m))
        }