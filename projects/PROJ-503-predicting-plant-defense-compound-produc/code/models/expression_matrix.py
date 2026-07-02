"""
ExpressionMatrix data model for gene expression data.

Represents a matrix of gene expression values (samples x genes) with metadata.
"""
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from pathlib import Path
import json

class ExpressionMatrix:
    """
    Container for gene expression data with metadata and validation.
    
    Attributes:
        data: DataFrame with samples as rows and genes as columns.
        metadata: Dictionary containing run-level metadata (e.g., accession, platform).
        gene_ids: List of gene identifiers.
        sample_ids: List of sample identifiers.
    """
    
    def __init__(
        self,
        data: Optional[pd.DataFrame] = None,
        metadata: Optional[Dict[str, Any]] = None,
        gene_ids: Optional[List[str]] = None,
        sample_ids: Optional[List[str]] = None,
    ):
        """
        Initialize an ExpressionMatrix.
        
        Args:
            data: DataFrame of expression values (samples x genes).
            metadata: Optional metadata dictionary.
            gene_ids: Optional list of gene IDs (used if data columns are not set).
            sample_ids: Optional list of sample IDs (used if data index is not set).
        """
        self.metadata = metadata or {}
        
        if data is not None:
            self.data = data.copy()
            if gene_ids:
                self.data.columns = gene_ids
            if sample_ids:
                self.data.index = sample_ids
        else:
            self.data = pd.DataFrame()
        
        # Validate dimensions match
        self._validate()

    def _validate(self) -> None:
        """Validate the matrix structure."""
        if not self.data.empty:
            if self.data.index.name is None:
                self.data.index.name = "sample_id"
            if self.data.columns.name is None:
                self.data.columns.name = "gene_id"

    @property
    def gene_ids(self) -> List[str]:
        """Return list of gene identifiers."""
        return list(self.data.columns)

    @property
    def sample_ids(self) -> List[str]:
        """Return list of sample identifiers."""
        return list(self.data.index)

    @property
    def shape(self) -> tuple:
        """Return (n_samples, n_genes)."""
        return self.data.shape

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "data": self.data.to_dict(orient="list"),
            "metadata": self.metadata,
            "gene_ids": self.gene_ids,
            "sample_ids": self.sample_ids,
            "shape": self.shape,
        }

    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> "ExpressionMatrix":
        """
        Create an ExpressionMatrix from a dictionary.
        
        Args:
            data_dict: Dictionary containing 'data', 'metadata', etc.
        
        Returns:
            New ExpressionMatrix instance.
        """
        df = pd.DataFrame(data_dict["data"])
        # Restore index/columns if stored separately or as part of dict
        if "sample_ids" in data_dict and data_dict["sample_ids"]:
            df.index = data_dict["sample_ids"]
        if "gene_ids" in data_dict and data_dict["gene_ids"]:
            df.columns = data_dict["gene_ids"]
        
        return cls(
            data=df,
            metadata=data_dict.get("metadata", {}),
        )

    def save(self, path: Path) -> None:
        """
        Save the matrix to a CSV file and metadata to JSON.
        
        Args:
            path: Path to the directory or base filename (without extension).
        """
        path = Path(path)
        if path.suffix:
            base_path = path.parent
            csv_path = path
            json_path = path.with_suffix(".json")
        else:
            base_path = path.parent
            csv_path = path / "expression_matrix.csv"
            json_path = path / "expression_matrix.json"
        
        self.data.to_csv(csv_path)
        with open(json_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "ExpressionMatrix":
        """
        Load a matrix from CSV and JSON files.
        
        Args:
            path: Path to the CSV file or directory containing CSV and JSON.
        
        Returns:
            Loaded ExpressionMatrix instance.
        """
        path = Path(path)
        if path.suffix == ".csv":
            csv_path = path
            json_path = path.with_suffix(".json")
        else:
            csv_path = path / "expression_matrix.csv"
            json_path = path / "expression_matrix.json"
        
        df = pd.read_csv(csv_path, index_col=0)
        
        with open(json_path, "r") as f:
            data_dict = json.load(f)
        
        return cls.from_dict(data_dict)
