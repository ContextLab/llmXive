"""
ExpressionMatrix class for handling gene expression data.
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
    Represents a matrix of gene expression values (genes x samples).
    
    Attributes:
        data (pd.DataFrame): Expression values with gene IDs as index and sample IDs as columns.
        metadata (Dict[str, Any]): Additional metadata about the matrix (e.g., normalization method).
    """
    
    def __init__(self, data: Optional[pd.DataFrame] = None, metadata: Optional[Dict[str, Any]] = None):
        self.data = data if data is not None else pd.DataFrame()
        self.metadata = metadata if metadata is not None else {}
        
        if not self.data.empty:
            self._validate_structure()

    def _validate_structure(self):
        """Validate that the dataframe has the expected structure."""
        if self.data.index.name != "gene_id" and "gene_id" not in self.data.columns:
            logger.warning("Index is not named 'gene_id'. Setting index name.")
            if self.data.index.name is None:
                self.data.index.name = "gene_id"
        
        # Ensure no duplicate gene IDs
        if self.data.index.duplicated().any():
            raise ValueError("Duplicate gene IDs found in expression matrix index.")

    def add_metadata(self, key: str, value: Any):
        """Add or update a metadata field."""
        self.metadata[key] = value
        logger.debug(f"Added metadata: {key} = {value}")

    def filter_genes(self, gene_ids: List[str]) -> "ExpressionMatrix":
        """
        Filter the matrix to keep only specified gene IDs.
        
        Args:
            gene_ids: List of gene IDs to keep.
        
        Returns:
            A new ExpressionMatrix instance with filtered data.
        """
        filtered_data = self.data.loc[self.data.index.intersection(gene_ids)]
        new_metadata = self.metadata.copy()
        new_metadata["filtered_genes"] = gene_ids
        return ExpressionMatrix(data=filtered_data, metadata=new_metadata)

    def filter_samples(self, sample_ids: List[str]) -> "ExpressionMatrix":
        """
        Filter the matrix to keep only specified sample IDs.
        
        Args:
            sample_ids: List of sample IDs to keep.
        
        Returns:
            A new ExpressionMatrix instance with filtered data.
        """
        filtered_data = self.data.loc[:, self.data.columns.intersection(sample_ids)]
        new_metadata = self.metadata.copy()
        new_metadata["filtered_samples"] = sample_ids
        return ExpressionMatrix(data=filtered_data, metadata=new_metadata)

    def normalize_per_species(self, species_map: Dict[str, str]) -> "ExpressionMatrix":
        """
        Apply Z-score normalization per species.
        
        Args:
            species_map: Dict mapping sample_id -> species_name.
        
        Returns:
            Normalized ExpressionMatrix.
        """
        if self.data.empty:
            return self

        normalized_data = self.data.copy()
        for species, samples in self._group_samples_by_species(species_map).items():
            if len(samples) > 1:
                subset = normalized_data.loc[:, [s for s in samples if s in normalized_data.columns]]
                if not subset.empty:
                    mean_val = subset.mean(axis=1)
                    std_val = subset.std(axis=1)
                    # Avoid division by zero
                    std_val[std_val == 0] = 1.0
                    normalized_data.loc[:, subset.columns] = (subset - mean_val) / std_val
        
        new_metadata = self.metadata.copy()
        new_metadata["normalization"] = "z_score_per_species"
        return ExpressionMatrix(data=normalized_data, metadata=new_metadata)

    def _group_samples_by_species(self, species_map: Dict[str, str]) -> Dict[str, List[str]]:
        """Group sample IDs by species."""
        groups = {}
        for sample_id, species in species_map.items():
            if sample_id in self.data.columns:
                groups.setdefault(species, []).append(sample_id)
        return groups

    def to_csv(self, path: str):
        """Save the matrix to a CSV file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.data.to_csv(path)
        # Save metadata separately as JSON
        metadata_path = Path(path).with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)
        logger.info(f"Saved expression matrix to {path}")

    @classmethod
    def from_csv(cls, path: str) -> "ExpressionMatrix":
        """Load a matrix from a CSV file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Expression matrix file not found: {path}")
        
        data = pd.read_csv(path, index_col=0)
        
        metadata = {}
        metadata_path = path.with_suffix('.json')
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        
        return cls(data=data, metadata=metadata)

    def __repr__(self):
        return f"ExpressionMatrix(shape={self.data.shape}, metadata_keys={list(self.metadata.keys())})"
