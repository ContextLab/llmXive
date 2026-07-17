import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class ExpressionMatrix:
    """
    Represents a gene expression matrix (genes x samples).
    
    Attributes:
        data: DataFrame with genes as index and samples as columns.
        metadata: Optional dictionary of sample-level metadata.
        source_info: Dictionary tracking data source (GEO accession, etc.).
    """
    
    def __init__(
        self,
        data: Optional[pd.DataFrame] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_info: Optional[Dict[str, Any]] = None
    ):
        self.data = data if data is not None else pd.DataFrame()
        self.metadata = metadata if metadata is not None else {}
        self.source_info = source_info if source_info is not None else {}
        
        if not self.data.empty:
            self._validate_shape()
    
    def _validate_shape(self):
        """Ensure data is a valid matrix (non-empty, numeric values)."""
        if self.data.empty:
            raise ValueError("ExpressionMatrix data cannot be empty.")
        
        # Ensure all values are numeric
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) != len(self.data.columns):
            non_numeric = set(self.data.columns) - set(numeric_cols)
            logger.warning(f"Non-numeric columns detected in expression data: {non_numeric}")
    
    def get_gene_ids(self) -> List[str]:
        """Return list of gene identifiers (index)."""
        return list(self.data.index)
    
    def get_sample_ids(self) -> List[str]:
        """Return list of sample identifiers (columns)."""
        return list(self.data.columns)
    
    def get_dimensions(self) -> tuple:
        """Return (n_genes, n_samples)."""
        return self.data.shape
    
    def filter_genes(self, gene_ids: List[str]) -> 'ExpressionMatrix':
        """Return a new ExpressionMatrix filtered to only include specified genes."""
        available = set(self.data.index)
        requested = set(gene_ids)
        missing = requested - available
        
        if missing:
            logger.warning(f"Genes not found in matrix: {len(missing)}")
        
        filtered_data = self.data.loc[list(available.intersection(requested))]
        return ExpressionMatrix(
            data=filtered_data,
            metadata=self.metadata.copy(),
            source_info=self.source_info.copy()
        )
    
    def filter_samples(self, sample_ids: List[str]) -> 'ExpressionMatrix':
        """Return a new ExpressionMatrix filtered to only include specified samples."""
        available = set(self.data.columns)
        requested = set(sample_ids)
        missing = requested - available
        
        if missing:
            logger.warning(f"Samples not found in matrix: {len(missing)}")
        
        filtered_data = self.data[list(available.intersection(requested))]
        return ExpressionMatrix(
            data=filtered_data,
            metadata=self.metadata.copy(),
            source_info=self.source_info.copy()
        )
    
    def to_csv(self, filepath: Path) -> None:
        """Save the expression matrix to a CSV file."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        self.data.to_csv(filepath)
        logger.info(f"Expression matrix saved to {filepath}")
    
    @classmethod
    def from_csv(cls, filepath: Path) -> 'ExpressionMatrix':
        """Load an expression matrix from a CSV file."""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Expression matrix file not found: {filepath}")
        
        data = pd.read_csv(filepath, index_col=0)
        return cls(data=data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the matrix to a dictionary representation for serialization."""
        return {
            "data": self.data.to_dict(orient="split"),
            "metadata": self.metadata,
            "source_info": self.source_info
        }
    
    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> 'ExpressionMatrix':
        """Reconstruct an ExpressionMatrix from a dictionary."""
        data = pd.DataFrame(
            data_dict["data"]["data"],
            index=data_dict["data"]["index"],
            columns=data_dict["data"]["columns"]
        )
        return cls(
            data=data,
            metadata=data_dict.get("metadata", {}),
            source_info=data_dict.get("source_info", {})
        )
    
    def __repr__(self) -> str:
        n_genes, n_samples = self.get_dimensions()
        return f"ExpressionMatrix(genes={n_genes}, samples={n_samples})"
