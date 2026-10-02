"""
Data loader module.
Defines the HarmonizedDataset dataclass for structured data access.
"""
from dataclasses import dataclass, field
from typing import Optional
import numpy as np
import pandas as pd
from pathlib import Path

@dataclass
class HarmonizedDataset:
    """
    Structured representation of harmonized force-vs-separation data.
    
    Attributes:
        separation_m: 1D array of separation distances in meters.
        force_N: 1D array of force measurements in Newtons.
        covariance_matrix: 2D array (N x N) of the covariance matrix.
        experiment_id: Identifier for the source experiment.
        metadata: Optional dictionary for additional metadata.
    """
    separation_m: np.ndarray
    force_N: np.ndarray
    covariance_matrix: np.ndarray
    experiment_id: str = ""
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        # Basic validation
        if len(self.separation_m) != len(self.force_N):
            raise ValueError("separation_m and force_N must have the same length.")
        if self.covariance_matrix.shape != (len(self.separation_m), len(self.separation_m)):
            raise ValueError("covariance_matrix shape must match (N, N).")

    def to_dict(self) -> dict:
        """Convert dataset to a dictionary (for JSON serialization)."""
        return {
            "separation_m": self.separation_m.tolist(),
            "force_N": self.force_N.tolist(),
            "covariance_matrix": self.covariance_matrix.tolist(),
            "experiment_id": self.experiment_id,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HarmonizedDataset":
        """Create dataset from a dictionary."""
        return cls(
            separation_m=np.array(data["separation_m"]),
            force_N=np.array(data["force_N"]),
            covariance_matrix=np.array(data["covariance_matrix"]),
            experiment_id=data.get("experiment_id", ""),
            metadata=data.get("metadata", {})
        )

def load_harmonized_data(file_path: Path) -> HarmonizedDataset:
    """
    Load a harmonized dataset from a JSON file.
    
    Args:
        file_path: Path to the JSON file.
    
    Returns:
        HarmonizedDataset object.
    """
    import json
    with open(file_path, 'r') as f:
        data = json.load(f)
    return HarmonizedDataset.from_dict(data)

def save_harmonized_data(dataset: HarmonizedDataset, file_path: Path):
    """
    Save a harmonized dataset to a JSON file.
    
    Args:
        dataset: HarmonizedDataset object.
        file_path: Path to save the JSON file.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(dataset.to_dict(), f, indent=2)

def main():
    """CLI entry point for loaders."""
    logger.info("Loaders module ready.")
    return 0

if __name__ == "__main__":
    exit(main())
