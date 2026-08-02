"""
ExpressionMatrix data model.

Represents gene expression data in WIDE FORMAT:
- Rows = genes
- Columns = samples
- Values = TPM (transcripts per million)

Attributes:
    gene_ids: List of unique gene identifiers (str)
    sample_ids: List of sample identifiers (str)
    values: 2D numpy array of expression values (numpy.float64)
"""
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

class ExpressionMatrix:
    """
    Data model for gene expression matrices in wide format.
    
    Format: Rows=genes, Columns=samples, values=TPM
    """
    
    def __init__(
        self,
        gene_ids: List[str],
        sample_ids: List[str],
        values: np.ndarray
    ):
        """
        Initialize an ExpressionMatrix.
        
        Args:
            gene_ids: List of unique gene identifiers.
            sample_ids: List of sample identifiers.
            values: 2D numpy array of shape (len(gene_ids), len(sample_ids)) 
                    with dtype numpy.float64.
        
        Raises:
            ValueError: If dimensions don't match, values aren't float64,
                        or gene_ids are not unique.
        """
        # Validate dimensions
        if len(gene_ids) != values.shape[0]:
            raise ValueError(
                f"gene_ids length ({len(gene_ids)}) must match values rows ({values.shape[0]})"
            )
        if len(sample_ids) != values.shape[1]:
            raise ValueError(
                f"sample_ids length ({len(sample_ids)}) must match values columns ({values.shape[1]})"
            )
        
        # Validate data types
        if values.dtype != np.float64:
            raise ValueError(f"values must be numpy.float64, got {values.dtype}")
        
        # Validate uniqueness
        if len(gene_ids) != len(set(gene_ids)):
            raise ValueError("gene_ids must be unique")
        
        if len(sample_ids) != len(set(sample_ids)):
            raise ValueError("sample_ids must be unique")
        
        self.gene_ids = gene_ids
        self.sample_ids = sample_ids
        self.values = values.astype(np.float64)
        
        logger.info(f"Created ExpressionMatrix with {len(gene_ids)} genes, {len(sample_ids)} samples")

    def to_csv(self, filepath: str, delimiter: str = ',') -> None:
        """
        Save the matrix to a CSV file.
        
        Format: WIDE FORMAT with column order: gene_id, sample_1, sample_2, ...
        NA handling: empty string for NaN values.
        
        Args:
            filepath: Path to output CSV file.
            delimiter: CSV delimiter (default ',').
        """
        # Create DataFrame
        df = pd.DataFrame(
            self.values,
            index=self.gene_ids,
            columns=self.sample_ids
        )
        
        # Insert gene_id as first column
        df.insert(0, 'gene_id', df.index)
        
        # Reset index to make it a column
        df = df.reset_index(drop=True)
        
        # Replace NaN with empty string
        df = df.fillna('')
        
        # Ensure numeric columns are formatted correctly (except gene_id)
        for col in df.columns[1:]:
            if df[col].dtype == object:
                # It's the gene_id column or mixed, skip
                continue
            # Format floats to avoid scientific notation for small numbers
            df[col] = df[col].apply(lambda x: f"{x:.10f}" if isinstance(x, (int, float)) else x)
        
        # Write to CSV
        df.to_csv(filepath, index=False, sep=delimiter, na_rep='')
        logger.info(f"Saved ExpressionMatrix to {filepath}")

    @classmethod
    def from_csv(cls, filepath: str, delimiter: str = ',') -> 'ExpressionMatrix':
        """
        Load an ExpressionMatrix from a CSV file.
        
        Args:
            filepath: Path to input CSV file.
            delimiter: CSV delimiter (default ',').
        
        Returns:
            ExpressionMatrix instance.
        
        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If CSV format is invalid.
        """
        if not Path(filepath).exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        df = pd.read_csv(filepath, delimiter=delimiter)
        
        # Validate structure
        if 'gene_id' not in df.columns:
            raise ValueError("CSV must contain 'gene_id' column")
        
        gene_ids = df['gene_id'].astype(str).tolist()
        sample_ids = [str(col) for col in df.columns if col != 'gene_id']
        
        # Extract values
        values_df = df.drop(columns=['gene_id'])
        
        # Convert to numpy array with float64
        values = values_df.to_numpy(dtype=np.float64)
        
        # Handle empty strings that might have been read as NaN
        values = np.where(values_df.isna().to_numpy(), np.nan, values)
        
        return cls(gene_ids=gene_ids, sample_ids=sample_ids, values=values)

    def get_shape(self) -> tuple:
        """Return (n_genes, n_samples)."""
        return self.values.shape

    def get_gene_ids(self) -> List[str]:
        """Return list of gene IDs."""
        return self.gene_ids.copy()

    def get_sample_ids(self) -> List[str]:
        """Return list of sample IDs."""
        return self.sample_ids.copy()

    def subset_by_genes(self, gene_ids: List[str]) -> 'ExpressionMatrix':
        """
        Create a new matrix with only the specified genes.
        
        Args:
            gene_ids: List of gene IDs to keep.
        
        Returns:
            New ExpressionMatrix with subset of genes.
        """
        indices = [self.gene_ids.index(gid) for gid in gene_ids if gid in self.gene_ids]
        if len(indices) != len(gene_ids):
            logger.warning(f"Some gene IDs not found: {set(gene_ids) - set(self.gene_ids)}")
        
        return ExpressionMatrix(
            gene_ids=[gid for gid in gene_ids if gid in self.gene_ids],
            sample_ids=self.sample_ids,
            values=self.values[indices, :]
        )

    def subset_by_samples(self, sample_ids: List[str]) -> 'ExpressionMatrix':
        """
        Create a new matrix with only the specified samples.
        
        Args:
            sample_ids: List of sample IDs to keep.
        
        Returns:
            New ExpressionMatrix with subset of samples.
        """
        indices = [self.sample_ids.index(sid) for sid in sample_ids if sid in self.sample_ids]
        if len(indices) != len(sample_ids):
            logger.warning(f"Some sample IDs not found: {set(sample_ids) - set(self.sample_ids)}")
        
        return ExpressionMatrix(
            gene_ids=self.gene_ids,
            sample_ids=[sid for sid in sample_ids if sid in self.sample_ids],
            values=self.values[:, indices]
        )
