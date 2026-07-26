"""
ExpressionMatrix data model class.

Represents a gene expression matrix with explicit attributes:
- gene_id: Identifier for the gene
- sample_id: Identifier for the biological sample
- value: Expression value (e.g., TPM, FPKM, or counts)
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
    Container for gene expression data.

    Attributes:
        data (pd.DataFrame): DataFrame with columns ['gene_id', 'sample_id', 'value']
    """

    REQUIRED_COLUMNS = ['gene_id', 'sample_id', 'value']

    def __init__(self, data: Optional[pd.DataFrame] = None):
        """
        Initialize ExpressionMatrix.

        Args:
            data: DataFrame with columns gene_id, sample_id, value.
                  If None, creates an empty DataFrame with required columns.
        """
        if data is None:
            self.data = pd.DataFrame(columns=self.REQUIRED_COLUMNS)
        else:
            self._validate_data(data)
            self.data = data.copy()

    def _validate_data(self, df: pd.DataFrame) -> None:
        """Validate that the DataFrame has the required columns."""
        missing = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(f"ExpressionMatrix requires columns {self.REQUIRED_COLUMNS}, missing: {missing}")

    @classmethod
    def load(cls, file_path: str) -> 'ExpressionMatrix':
        """
        Load expression matrix from a CSV file.

        Args:
            file_path: Path to the CSV file.

        Returns:
            ExpressionMatrix instance.
        """
        logger.info(f"Loading expression matrix from {file_path}")
        df = pd.read_csv(file_path)
        return cls(df)

    def save(self, file_path: str) -> None:
        """
        Save expression matrix to a CSV file.

        Args:
            file_path: Path to save the CSV file.
        """
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        self.data.to_csv(file_path, index=False)
        logger.info(f"Saved expression matrix to {file_path}")

    def filter_by_samples(self, sample_ids: List[str]) -> 'ExpressionMatrix':
        """
        Filter the matrix to keep only specified sample IDs.

        Args:
            sample_ids: List of sample IDs to keep.

        Returns:
            New ExpressionMatrix instance with filtered data.
        """
        filtered = self.data[self.data['sample_id'].isin(sample_ids)]
        return ExpressionMatrix(filtered)

    def filter_by_genes(self, gene_ids: List[str]) -> 'ExpressionMatrix':
        """
        Filter the matrix to keep only specified gene IDs.

        Args:
            gene_ids: List of gene IDs to keep.

        Returns:
            New ExpressionMatrix instance with filtered data.
        """
        filtered = self.data[self.data['gene_id'].isin(gene_ids)]
        return ExpressionMatrix(filtered)

    def to_pivot(self) -> pd.DataFrame:
        """
        Convert long-form data to a wide pivot table (genes x samples).

        Returns:
            DataFrame with gene_id as index and sample_id as columns.
        """
        return self.data.pivot(index='gene_id', columns='sample_id', values='value')

    @classmethod
    def from_pivot(cls, pivot_df: pd.DataFrame) -> 'ExpressionMatrix':
        """
        Create an ExpressionMatrix from a wide pivot DataFrame.

        Args:
            pivot_df: DataFrame with genes as index and samples as columns.

        Returns:
            ExpressionMatrix instance in long format.
        """
        df = pivot_df.reset_index()
        df_long = df.melt(id_vars=['gene_id'], var_name='sample_id', value_name='value')
        return cls(df_long)

    def get_unique_genes(self) -> List[str]:
        """Return a list of unique gene IDs."""
        return self.data['gene_id'].unique().tolist()

    def get_unique_samples(self) -> List[str]:
        """Return a list of unique sample IDs."""
        return self.data['sample_id'].unique().tolist()

    def __len__(self) -> int:
        """Return the number of rows in the matrix."""
        return len(self.data)

    def __repr__(self) -> str:
        return f"ExpressionMatrix(n_genes={len(self.get_unique_genes())}, n_samples={len(self.get_unique_samples())}, n_rows={len(self)})"
