"""
Data model for Gene Expression Matrices.

This module defines the schema for the ExpressionMatrix class.
It serves as a container for count data and associated metadata
generated from RNA-seq quantification (e.g., Salmon).

Note: This class defines the structure and validation logic only.
It does not instantiate or load real data; data loading is handled
by the ingestion and quantification pipelines (T015-T021).
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
from pathlib import Path

@dataclass
class ExpressionMatrix:
    """
    Represents a gene expression count matrix with associated sample metadata.

    Attributes:
        counts (pd.DataFrame): A DataFrame where rows are genes (transcripts)
            and columns are sample IDs. Values are raw integer counts.
        gene_ids (List[str]): List of unique gene/transcript identifiers.
        sample_ids (List[str]): List of unique sample identifiers.
        metadata (Optional[Dict[str, Any]]): Optional dictionary containing
            global metadata about the matrix (e.g., source, creation date,
            quantification tool version).
        is_normalized (bool): Flag indicating if the counts have been
            normalized (e.g., TPM, FPKM). Default is False for raw counts.
    """
    counts: pd.DataFrame
    gene_ids: List[str] = field(default_factory=list)
    sample_ids: List[str] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    is_normalized: bool = False

    def __post_init__(self):
        """
        Validates and initializes derived attributes after dataclass creation.
        """
        if self.counts is not None:
            # Ensure counts is a DataFrame
            if not isinstance(self.counts, pd.DataFrame):
                raise TypeError("counts must be a pandas DataFrame")

            # Auto-populate IDs if not provided or if they differ from DataFrame
            if not self.gene_ids:
                self.gene_ids = list(self.counts.index)
            if not self.sample_ids:
                self.sample_ids = list(self.counts.columns)

            # Validate dimensions match provided IDs
            if len(self.gene_ids) != len(self.counts.index):
                raise ValueError("Length of gene_ids does not match DataFrame index")
            if len(self.sample_ids) != len(self.counts.columns):
                raise ValueError("Length of sample_ids does not match DataFrame columns")

            # Validate data types (should be numeric)
            if not np.issubdtype(self.counts.values.dtype, np.number):
                # Allow mixed numeric types but warn or coerce if necessary
                # For strict count data, we expect integers, but pandas might infer float
                pass

    @classmethod
    def from_csv(cls, file_path: str, index_col: int = 0) -> "ExpressionMatrix":
        """
        Factory method to load an expression matrix from a CSV file.

        Args:
            file_path: Path to the CSV file containing the matrix.
            index_col: Column index to use as the row labels (gene IDs).

        Returns:
            An ExpressionMatrix instance.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file format is invalid.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Expression matrix file not found: {file_path}")

        df = pd.read_csv(file_path, index_col=index_col)
        return cls(counts=df)

    def filter_genes(self, min_count: int = 0, min_samples: int = 1) -> "ExpressionMatrix":
        """
        Returns a new ExpressionMatrix with genes filtered based on count thresholds.

        Args:
            min_count: Minimum count value required in a sample for the gene to be considered.
            min_samples: Minimum number of samples that must meet the min_count threshold.

        Returns:
            A new ExpressionMatrix instance with filtered rows.
        """
        # Count how many samples meet the threshold for each gene
        mask = self.counts >= min_count
        sample_counts = mask.sum(axis=1)

        # Keep genes that meet the sample count requirement
        valid_genes = sample_counts[sample_counts >= min_samples].index
        filtered_counts = self.counts.loc[valid_genes]

        return ExpressionMatrix(
            counts=filtered_counts,
            gene_ids=list(valid_genes),
            sample_ids=self.sample_ids,
            metadata=self.metadata,
            is_normalized=self.is_normalized
        )

    def to_csv(self, file_path: str) -> None:
        """
        Saves the expression matrix to a CSV file.

        Args:
            file_path: Destination path for the CSV file.
        """
        self.counts.to_csv(file_path)

    def get_summary(self) -> Dict[str, Any]:
        """
        Returns a summary dictionary of the matrix statistics.

        Returns:
            Dict containing shape, mean counts, and metadata status.
        """
        return {
            "n_genes": len(self.gene_ids),
            "n_samples": len(self.sample_ids),
            "total_counts": int(self.counts.sum().sum()),
            "mean_count_per_gene": float(self.counts.mean().mean()),
            "is_normalized": self.is_normalized,
            "has_metadata": self.metadata is not None
        }
