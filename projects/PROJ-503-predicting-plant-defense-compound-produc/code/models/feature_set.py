"""
FeatureSet data model for selected gene features.

Represents a subset of genes selected for modeling (e.g., pathway-specific genes).
"""
import pandas as pd
from typing import Optional, List, Dict, Any
from pathlib import Path
import json

class FeatureSet:
    """
    Container for a set of selected features (genes) with associated metadata.
    
    Attributes:
        gene_ids: List of gene identifiers included in this set.
        metadata: Dictionary containing selection criteria (e.g., pathway, method).
    """
    
    def __init__(
        self,
        gene_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a FeatureSet.
        
        Args:
            gene_ids: List of gene identifiers.
            metadata: Optional metadata dictionary.
        """
        self.gene_ids = gene_ids or []
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "gene_ids": self.gene_ids,
            "metadata": self.metadata,
            "n_features": len(self.gene_ids),
        }

    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> "FeatureSet":
        """
        Create a FeatureSet from a dictionary.
        
        Args:
            data_dict: Dictionary containing 'gene_ids', 'metadata', etc.
        
        Returns:
            New FeatureSet instance.
        """
        return cls(
            gene_ids=data_dict.get("gene_ids", []),
            metadata=data_dict.get("metadata", {}),
        )

    def save(self, path: Path) -> None:
        """
        Save the feature set to a JSON file.
        
        Args:
            path: Path to the output file.
        """
        path = Path(path)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "FeatureSet":
        """
        Load a feature set from a JSON file.
        
        Args:
            path: Path to the input file.
        
        Returns:
            Loaded FeatureSet instance.
        """
        path = Path(path)
        with open(path, "r") as f:
            data_dict = json.load(f)
        return cls.from_dict(data_dict)

    def filter_by_pathway(self, pathway_ids: List[str]) -> "FeatureSet":
        """
        Create a new FeatureSet filtered by pathway IDs (if pathway metadata exists).
        
        Args:
            pathway_ids: List of pathway identifiers to filter by.
        
        Returns:
            New filtered FeatureSet.
        """
        # This is a placeholder; actual filtering logic depends on how pathway info is stored.
        # For now, we return a copy assuming the list is already filtered or metadata is external.
        return FeatureSet(gene_ids=self.gene_ids.copy(), metadata=self.metadata.copy())
