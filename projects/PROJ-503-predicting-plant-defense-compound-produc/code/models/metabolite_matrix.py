"""
MetaboliteMatrix data model class.

Represents a metabolite concentration matrix with explicit attributes:
- metabolite_id: Identifier for the metabolite
- sample_id: Identifier for the biological sample
- value: Concentration value (e.g., log-transformed or raw)
"""
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class MetaboliteMatrix:
    """
    Container for metabolite concentration data.

    Attributes:
        data (pd.DataFrame): DataFrame with columns ['metabolite_id', 'sample_id', 'value']
    """

    REQUIRED_COLUMNS = ['metabolite_id', 'sample_id', 'value']

    def __init__(self, data: Optional[pd.DataFrame] = None):
        """
        Initialize MetaboliteMatrix.

        Args:
            data: DataFrame with columns metabolite_id, sample_id, value.
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
            raise ValueError(f"MetaboliteMatrix requires columns {self.REQUIRED_COLUMNS}, missing: {missing}")

    @classmethod
    def load(cls, file_path: str) -> 'MetaboliteMatrix':
        """
        Load metabolite matrix from a CSV file.

        Args:
            file_path: Path to the CSV file.

        Returns:
            MetaboliteMatrix instance.
        """
        logger.info(f"Loading metabolite matrix from {file_path}")
        df = pd.read_csv(file_path)
        return cls(df)

    def save(self, file_path: str) -> None:
        """
        Save metabolite matrix to a CSV file.

        Args:
            file_path: Path to save the CSV file.
        """
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        self.data.to_csv(file_path, index=False)
        logger.info(f"Saved metabolite matrix to {file_path}")

    def filter_by_samples(self, sample_ids: List[str]) -> 'MetaboliteMatrix':
        """
        Filter the matrix to keep only specified sample IDs.

        Args:
            sample_ids: List of sample IDs to keep.

        Returns:
            New MetaboliteMatrix instance with filtered data.
        """
        filtered = self.data[self.data['sample_id'].isin(sample_ids)]
        return MetaboliteMatrix(filtered)

    def filter_by_metabolites(self, metabolite_ids: List[str]) -> 'MetaboliteMatrix':
        """
        Filter the matrix to keep only specified metabolite IDs.

        Args:
            metabolite_ids: List of metabolite IDs to keep.

        Returns:
            New MetaboliteMatrix instance with filtered data.
        """
        filtered = self.data[self.data['metabolite_id'].isin(metabolite_ids)]
        return MetaboliteMatrix(filtered)

    def to_pivot(self) -> pd.DataFrame:
        """
        Convert long-form data to a wide pivot table (metabolites x samples).

        Returns:
            DataFrame with metabolite_id as index and sample_id as columns.
        """
        return self.data.pivot(index='metabolite_id', columns='sample_id', values='value')

    @classmethod
    def from_pivot(cls, pivot_df: pd.DataFrame) -> 'MetaboliteMatrix':
        """
        Create a MetaboliteMatrix from a wide pivot DataFrame.

        Args:
            pivot_df: DataFrame with metabolites as index and samples as columns.

        Returns:
            MetaboliteMatrix instance in long format.
        """
        df = pivot_df.reset_index()
        df_long = df.melt(id_vars=['metabolite_id'], var_name='sample_id', value_name='value')
        return cls(df_long)

    def get_unique_metabolites(self) -> List[str]:
        """Return a list of unique metabolite IDs."""
        return self.data['metabolite_id'].unique().tolist()

    def get_unique_samples(self) -> List[str]:
        """Return a list of unique sample IDs."""
        return self.data['sample_id'].unique().tolist()

    def __len__(self) -> int:
        """Return the number of rows in the matrix."""
        return len(self.data)

    def __repr__(self) -> str:
        return f"MetaboliteMatrix(n_metabolites={len(self.get_unique_metabolites())}, n_samples={len(self.get_unique_samples())}, n_rows={len(self)})"
