"""
FeatureSet data model class.

Represents a subset of features (genes) selected for modeling,
typically filtered by pathway membership or variance.
"""
import pandas as pd
from typing import Optional, List, Dict, Any, Set
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class FeatureSet:
    """
    Container for a set of selected features (genes).

    Attributes:
        gene_ids (Set[str]): Set of gene identifiers included in this feature set.
        metadata (Dict[str, Any]): Optional metadata (e.g., pathway names, selection method).
    """

    def __init__(self, gene_ids: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize FeatureSet.

        Args:
            gene_ids: List of gene IDs to include.
            metadata: Optional dictionary of metadata.
        """
        self.gene_ids = set(gene_ids) if gene_ids else set()
        self.metadata = metadata or {}

    def add_gene(self, gene_id: str) -> None:
        """Add a gene to the set."""
        self.gene_ids.add(gene_id)

    def remove_gene(self, gene_id: str) -> None:
        """Remove a gene from the set."""
        self.gene_ids.discard(gene_id)

    def contains(self, gene_id: str) -> bool:
        """Check if a gene is in the set."""
        return gene_id in self.gene_ids

    def to_list(self) -> List[str]:
        """Return the gene IDs as a list."""
        return list(self.gene_ids)

    def save(self, file_path: str) -> None:
        """
        Save the feature set to a JSON file.

        Args:
            file_path: Path to save the JSON file.
        """
        data = {
            'gene_ids': sorted(list(self.gene_ids)),
            'metadata': self.metadata
        }
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved FeatureSet with {len(self.gene_ids)} genes to {file_path}")

    @classmethod
    def load(cls, file_path: str) -> 'FeatureSet':
        """
        Load a feature set from a JSON file.

        Args:
            file_path: Path to the JSON file.

        Returns:
            FeatureSet instance.
        """
        logger.info(f"Loading FeatureSet from {file_path}")
        with open(file_path, 'r') as f:
            data = json.load(f)
        return cls(gene_ids=data.get('gene_ids', []), metadata=data.get('metadata', {}))

    def intersect(self, other: 'FeatureSet') -> 'FeatureSet':
        """
        Return a new FeatureSet containing the intersection with another.

        Args:
            other: Another FeatureSet.

        Returns:
            New FeatureSet with common genes.
        """
        common = self.gene_ids.intersection(other.gene_ids)
        return FeatureSet(gene_ids=list(common), metadata={'source': 'intersection'})

    def union(self, other: 'FeatureSet') -> 'FeatureSet':
        """
        Return a new FeatureSet containing the union with another.

        Args:
            other: Another FeatureSet.

        Returns:
            New FeatureSet with all unique genes.
        """
        all_genes = self.gene_ids.union(other.gene_ids)
        return FeatureSet(gene_ids=list(all_genes), metadata={'source': 'union'})

    def difference(self, other: 'FeatureSet') -> 'FeatureSet':
        """
        Return a new FeatureSet containing genes in self but not in other.

        Args:
            other: Another FeatureSet.

        Returns:
            New FeatureSet with difference.
        """
        diff = self.gene_ids.difference(other.gene_ids)
        return FeatureSet(gene_ids=list(diff), metadata={'source': 'difference'})

    def __len__(self) -> int:
        """Return the number of genes in the set."""
        return len(self.gene_ids)

    def __repr__(self) -> str:
        return f"FeatureSet(n_genes={len(self.gene_ids)}, metadata={self.metadata})"
