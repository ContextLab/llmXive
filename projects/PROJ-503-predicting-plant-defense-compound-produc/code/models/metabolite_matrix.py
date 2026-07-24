"""
MetaboliteMatrix class for handling metabolite concentration data.
"""
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import logging
import math

logger = logging.getLogger(__name__)

class MetaboliteMatrix:
    """
    Represents a matrix of metabolite concentrations (metabolites x samples).
    
    Attributes:
        data (pd.DataFrame): Concentration values with metabolite IDs as index and sample IDs as columns.
        metadata (Dict[str, Any]): Additional metadata (e.g., transformation method).
    """
    
    def __init__(self, data: Optional[pd.DataFrame] = None, metadata: Optional[Dict[str, Any]] = None):
        self.data = data if data is not None else pd.DataFrame()
        self.metadata = metadata if metadata is not None else {}
        
        if not self.data.empty:
            self._validate_structure()

    def _validate_structure(self):
        """Validate that the dataframe has the expected structure."""
        if self.data.index.name != "metabolite_id" and "metabolite_id" not in self.data.columns:
            logger.warning("Index is not named 'metabolite_id'. Setting index name.")
            if self.data.index.name is None:
                self.data.index.name = "metabolite_id"
        
        if self.data.index.duplicated().any():
            raise ValueError("Duplicate metabolite IDs found in metabolite matrix index.")

    def add_metadata(self, key: str, value: Any):
        """Add or update a metadata field."""
        self.metadata[key] = value
        logger.debug(f"Added metadata: {key} = {value}")

    def log_transform(self, base: float = np.e, offset: float = 1.0) -> "MetaboliteMatrix":
        """
        Apply log transformation to the data.
        
        Args:
            base: Log base (default e).
            offset: Value to add before log to avoid log(0).
        
        Returns:
            Transformed MetaboliteMatrix.
        """
        if self.data.empty:
            return self

        transformed_data = np.log(self.data + offset) / np.log(base)
        new_metadata = self.metadata.copy()
        new_metadata["transformation"] = f"log_{base}_with_offset_{offset}"
        return MetaboliteMatrix(data=pd.DataFrame(transformed_data, index=self.data.index, columns=self.data.columns), 
                                metadata=new_metadata)

    def filter_metabolites(self, metabolite_ids: List[str]) -> "MetaboliteMatrix":
        """
        Filter the matrix to keep only specified metabolite IDs.
        
        Args:
            metabolite_ids: List of metabolite IDs to keep.
        
        Returns:
            A new MetaboliteMatrix instance with filtered data.
        """
        filtered_data = self.data.loc[self.data.index.intersection(metabolite_ids)]
        new_metadata = self.metadata.copy()
        new_metadata["filtered_metabolites"] = metabolite_ids
        return MetaboliteMatrix(data=filtered_data, metadata=new_metadata)

    def filter_samples(self, sample_ids: List[str]) -> "MetaboliteMatrix":
        """
        Filter the matrix to keep only specified sample IDs.
        
        Args:
            sample_ids: List of sample IDs to keep.
        
        Returns:
            A new MetaboliteMatrix instance with filtered data.
        """
        filtered_data = self.data.loc[:, self.data.columns.intersection(sample_ids)]
        new_metadata = self.metadata.copy()
        new_metadata["filtered_samples"] = sample_ids
        return MetaboliteMatrix(data=filtered_data, metadata=new_metadata)

    def to_csv(self, path: str):
        """Save the matrix to a CSV file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.data.to_csv(path)
        # Save metadata separately as JSON
        metadata_path = Path(path).with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)
        logger.info(f"Saved metabolite matrix to {path}")

    @classmethod
    def from_csv(cls, path: str) -> "MetaboliteMatrix":
        """Load a matrix from a CSV file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Metabolite matrix file not found: {path}")
        
        data = pd.read_csv(path, index_col=0)
        
        metadata = {}
        metadata_path = path.with_suffix('.json')
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        
        return cls(data=data, metadata=metadata)

    def __repr__(self):
        return f"MetaboliteMatrix(shape={self.data.shape}, metadata_keys={list(self.metadata.keys())})"
