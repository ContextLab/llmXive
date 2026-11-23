"""
MetaboliteMatrix data model.

Represents metabolite concentration data in WIDE FORMAT:
- Rows = metabolites
- Columns = samples
- Values = log-concentration (log-transformed)

Attributes:
    metabolite_ids: List of unique metabolite identifiers (str)
    sample_ids: List of sample identifiers (str)
    values: 2D numpy array of log-concentration values (numpy.float64)
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
    Data model for metabolite concentration matrices in wide format.
    
    Format: Rows=metabolites, Columns=samples, values=log-concentration
    """
    
    def __init__(
        self,
        metabolite_ids: List[str],
        sample_ids: List[str],
        values: np.ndarray
    ):
        """
        Initialize a MetaboliteMatrix.
        
        Args:
            metabolite_ids: List of unique metabolite identifiers.
            sample_ids: List of sample identifiers.
            values: 2D numpy array of shape (len(metabolite_ids), len(sample_ids))
                    with dtype numpy.float64.
        
        Raises:
            ValueError: If dimensions don't match, values aren't float64,
                        or metabolite_ids are not unique.
        """
        # Validate dimensions
        if len(metabolite_ids) != values.shape[0]:
            raise ValueError(
                f"metabolite_ids length ({len(metabolite_ids)}) must match values rows ({values.shape[0]})"
            )
        if len(sample_ids) != values.shape[1]:
            raise ValueError(
                f"sample_ids length ({len(sample_ids)}) must match values columns ({values.shape[1]})"
            )
        
        # Validate data types
        if values.dtype != np.float64:
            raise ValueError(f"values must be numpy.float64, got {values.dtype}")
        
        # Validate uniqueness
        if len(metabolite_ids) != len(set(metabolite_ids)):
            raise ValueError("metabolite_ids must be unique")
        
        if len(sample_ids) != len(set(sample_ids)):
            raise ValueError("sample_ids must be unique")
        
        self.metabolite_ids = metabolite_ids
        self.sample_ids = sample_ids
        self.values = values.astype(np.float64)
        
        logger.info(f"Created MetaboliteMatrix with {len(metabolite_ids)} metabolites, {len(sample_ids)} samples")

    def to_csv(self, filepath: str, delimiter: str = ',') -> None:
        """
        Save the matrix to a CSV file.
        
        Format: WIDE FORMAT with column order: metabolite_id, sample_1, sample_2, ...
        NA handling: empty string for NaN values.
        
        Args:
            filepath: Path to output CSV file.
            delimiter: CSV delimiter (default ',').
        """
        # Create DataFrame
        df = pd.DataFrame(
            self.values,
            index=self.metabolite_ids,
            columns=self.sample_ids
        )
        
        # Insert metabolite_id as first column
        df.insert(0, 'metabolite_id', df.index)
        
        # Reset index to make it a column
        df = df.reset_index(drop=True)
        
        # Replace NaN with empty string
        df = df.fillna('')
        
        # Ensure numeric columns are formatted correctly (except metabolite_id)
        for col in df.columns[1:]:
            if df[col].dtype == object:
                continue
            df[col] = df[col].apply(lambda x: f"{x:.10f}" if isinstance(x, (int, float)) else x)
        
        # Write to CSV
        df.to_csv(filepath, index=False, sep=delimiter, na_rep='')
        logger.info(f"Saved MetaboliteMatrix to {filepath}")

    @classmethod
    def from_csv(cls, filepath: str, delimiter: str = ',') -> 'MetaboliteMatrix':
        """
        Load a MetaboliteMatrix from a CSV file.
        
        Args:
            filepath: Path to input CSV file.
            delimiter: CSV delimiter (default ',').
        
        Returns:
            MetaboliteMatrix instance.
        
        Raises:
            FileNotFoundError: If file doesn't exist.
            ValueError: If CSV format is invalid.
        """
        if not Path(filepath).exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        df = pd.read_csv(filepath, delimiter=delimiter)
        
        # Validate structure
        if 'metabolite_id' not in df.columns:
            raise ValueError("CSV must contain 'metabolite_id' column")
        
        metabolite_ids = df['metabolite_id'].astype(str).tolist()
        sample_ids = [str(col) for col in df.columns if col != 'metabolite_id']
        
        # Extract values
        values_df = df.drop(columns=['metabolite_id'])
        
        # Convert to numpy array with float64
        values = values_df.to_numpy(dtype=np.float64)
        
        # Handle empty strings that might have been read as NaN
        values = np.where(values_df.isna().to_numpy(), np.nan, values)
        
        return cls(metabolite_ids=metabolite_ids, sample_ids=sample_ids, values=values)

    def get_shape(self) -> tuple:
        """Return (n_metabolites, n_samples)."""
        return self.values.shape

    def get_metabolite_ids(self) -> List[str]:
        """Return list of metabolite IDs."""
        return self.metabolite_ids.copy()

    def get_sample_ids(self) -> List[str]:
        """Return list of sample IDs."""
        return self.sample_ids.copy()

    def subset_by_metabolites(self, metabolite_ids: List[str]) -> 'MetaboliteMatrix':
        """
        Create a new matrix with only the specified metabolites.
        
        Args:
            metabolite_ids: List of metabolite IDs to keep.
        
        Returns:
            New MetaboliteMatrix with subset of metabolites.
        """
        indices = [self.metabolite_ids.index(mid) for mid in metabolite_ids if mid in self.metabolite_ids]
        if len(indices) != len(metabolite_ids):
            logger.warning(f"Some metabolite IDs not found: {set(metabolite_ids) - set(self.metabolite_ids)}")
        
        return MetaboliteMatrix(
            metabolite_ids=[mid for mid in metabolite_ids if mid in self.metabolite_ids],
            sample_ids=self.sample_ids,
            values=self.values[indices, :]
        )

    def subset_by_samples(self, sample_ids: List[str]) -> 'MetaboliteMatrix':
        """
        Create a new matrix with only the specified samples.
        
        Args:
            sample_ids: List of sample IDs to keep.
        
        Returns:
            New MetaboliteMatrix with subset of samples.
        """
        indices = [self.sample_ids.index(sid) for sid in sample_ids if sid in self.sample_ids]
        if len(indices) != len(sample_ids):
            logger.warning(f"Some sample IDs not found: {set(sample_ids) - set(self.sample_ids)}")
        
        return MetaboliteMatrix(
            metabolite_ids=self.metabolite_ids,
            sample_ids=[sid for sid in sample_ids if sid in self.sample_ids],
            values=self.values[:, indices]
        )
