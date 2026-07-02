"""
MetaboliteMatrix data model for metabolite concentration data.

Represents a matrix of metabolite concentrations (samples x metabolites) with metadata.
"""
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from pathlib import Path
import json

class MetaboliteMatrix:
    """
    Container for metabolite concentration data with metadata and validation.
    
    Attributes:
        data: DataFrame with samples as rows and metabolites as columns.
        metadata: Dictionary containing run-level metadata (e.g., accession, platform).
        metabolite_ids: List of metabolite identifiers.
        sample_ids: List of sample identifiers.
    """
    
    def __init__(
        self,
        data: Optional[pd.DataFrame] = None,
        metadata: Optional[Dict[str, Any]] = None,
        metabolite_ids: Optional[List[str]] = None,
        sample_ids: Optional[List[str]] = None,
    ):
        """
        Initialize a MetaboliteMatrix.
        
        Args:
            data: DataFrame of concentration values (samples x metabolites).
            metadata: Optional metadata dictionary.
            metabolite_ids: Optional list of metabolite IDs.
            sample_ids: Optional list of sample IDs.
        """
        self.metadata = metadata or {}
        
        if data is not None:
            self.data = data.copy()
            if metabolite_ids:
                self.data.columns = metabolite_ids
            if sample_ids:
                self.data.index = sample_ids
        else:
            self.data = pd.DataFrame()
        
        self._validate()

    def _validate(self) -> None:
        """Validate the matrix structure."""
        if not self.data.empty:
            if self.data.index.name is None:
                self.data.index.name = "sample_id"
            if self.data.columns.name is None:
                self.data.columns.name = "metabolite_id"

    @property
    def metabolite_ids(self) -> List[str]:
        """Return list of metabolite identifiers."""
        return list(self.data.columns)

    @property
    def sample_ids(self) -> List[str]:
        """Return list of sample identifiers."""
        return list(self.data.index)

    @property
    def shape(self) -> tuple:
        """Return (n_samples, n_metabolites)."""
        return self.data.shape

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "data": self.data.to_dict(orient="list"),
            "metadata": self.metadata,
            "metabolite_ids": self.metabolite_ids,
            "sample_ids": self.sample_ids,
            "shape": self.shape,
        }

    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> "MetaboliteMatrix":
        """
        Create a MetaboliteMatrix from a dictionary.
        
        Args:
            data_dict: Dictionary containing 'data', 'metadata', etc.
        
        Returns:
            New MetaboliteMatrix instance.
        """
        df = pd.DataFrame(data_dict["data"])
        if "sample_ids" in data_dict and data_dict["sample_ids"]:
            df.index = data_dict["sample_ids"]
        if "metabolite_ids" in data_dict and data_dict["metabolite_ids"]:
            df.columns = data_dict["metabolite_ids"]
        
        return cls(
            data=df,
            metadata=data_dict.get("metadata", {}),
        )

    def save(self, path: Path) -> None:
        """
        Save the matrix to a CSV file and metadata to JSON.
        
        Args:
            path: Path to the directory or base filename.
        """
        path = Path(path)
        if path.suffix:
            csv_path = path
            json_path = path.with_suffix(".json")
        else:
            csv_path = path / "metabolite_matrix.csv"
            json_path = path / "metabolite_matrix.json"
        
        self.data.to_csv(csv_path)
        with open(json_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "MetaboliteMatrix":
        """
        Load a matrix from CSV and JSON files.
        
        Args:
            path: Path to the CSV file or directory.
        
        Returns:
            Loaded MetaboliteMatrix instance.
        """
        path = Path(path)
        if path.suffix == ".csv":
            csv_path = path
            json_path = path.with_suffix(".json")
        else:
            csv_path = path / "metabolite_matrix.csv"
            json_path = path / "metabolite_matrix.json"
        
        df = pd.read_csv(csv_path, index_col=0)
        
        with open(json_path, "r") as f:
            data_dict = json.load(f)
        
        return cls.from_dict(data_dict)
