"""
FeatureSet data model.

Represents a subset of features (genes) selected for modeling.
Contains gene IDs and their associated metadata (e.g., pathway mapping).

Attributes:
    gene_ids: List of gene identifiers included in this feature set
    pathway_mapping: Dict mapping gene_id to pathway information
    source_matrix: Optional reference to the parent ExpressionMatrix
"""
import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any, Set
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

class FeatureSet:
    """
    Data model for a selected set of features (genes).
    """
    
    def __init__(
        self,
        gene_ids: List[str],
        pathway_mapping: Optional[Dict[str, str]] = None,
        source_matrix: Optional[Any] = None
    ):
        """
        Initialize a FeatureSet.
        
        Args:
            gene_ids: List of gene identifiers included in this set.
            pathway_mapping: Optional dict mapping gene_id to pathway name.
            source_matrix: Optional reference to parent ExpressionMatrix.
        
        Raises:
            ValueError: If gene_ids are not unique.
        """
        if len(gene_ids) != len(set(gene_ids)):
            raise ValueError("gene_ids must be unique")
        
        self.gene_ids = gene_ids
        self.pathway_mapping = pathway_mapping or {}
        self.source_matrix = source_matrix
        
        logger.info(f"Created FeatureSet with {len(gene_ids)} genes")

    def to_csv(self, filepath: str) -> None:
        """
        Save the feature set to a CSV file.
        
        Format: gene_id, pathway
        
        Args:
            filepath: Path to output CSV file.
        """
        data = []
        for gid in self.gene_ids:
            pathway = self.pathway_mapping.get(gid, '')
            data.append({'gene_id': gid, 'pathway': pathway})
        
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        logger.info(f"Saved FeatureSet to {filepath}")

    @classmethod
    def from_csv(
        cls, 
        filepath: str, 
        source_matrix: Optional[Any] = None
    ) -> 'FeatureSet':
        """
        Load a FeatureSet from a CSV file.
        
        Args:
            filepath: Path to input CSV file.
            source_matrix: Optional reference to parent ExpressionMatrix.
        
        Returns:
            FeatureSet instance.
        """
        if not Path(filepath).exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        df = pd.read_csv(filepath)
        
        if 'gene_id' not in df.columns:
            raise ValueError("CSV must contain 'gene_id' column")
        
        gene_ids = df['gene_id'].astype(str).tolist()
        
        pathway_mapping = {}
        if 'pathway' in df.columns:
            for _, row in df.iterrows():
                pathway_mapping[row['gene_id']] = row['pathway'] if pd.notna(row['pathway']) else ''
        
        return cls(gene_ids=gene_ids, pathway_mapping=pathway_mapping, source_matrix=source_matrix)

    def get_gene_ids(self) -> List[str]:
        """Return list of gene IDs in this feature set."""
        return self.gene_ids.copy()

    def get_pathway_mapping(self) -> Dict[str, str]:
        """Return the pathway mapping dictionary."""
        return self.pathway_mapping.copy()

    def get_genes_by_pathway(self, pathway: str) -> List[str]:
        """
        Get all genes belonging to a specific pathway.
        
        Args:
            pathway: Pathway name to filter by.
        
        Returns:
            List of gene IDs in the specified pathway.
        """
        return [gid for gid, p in self.pathway_mapping.items() if p == pathway]

    def filter_by_pathway(self, pathways: List[str]) -> 'FeatureSet':
        """
        Create a new FeatureSet with only genes from specified pathways.
        
        Args:
            pathways: List of pathway names to keep.
        
        Returns:
            New FeatureSet with filtered genes.
        """
        filtered_genes = [
            gid for gid in self.gene_ids 
            if self.pathway_mapping.get(gid, '') in pathways
        ]
        filtered_mapping = {
            gid: self.pathway_mapping[gid] 
            for gid in filtered_genes
        }
        
        return FeatureSet(
            gene_ids=filtered_genes,
            pathway_mapping=filtered_mapping,
            source_matrix=self.source_matrix
        )

    def get_expression_matrix(self) -> Optional[Any]:
        """
        Get the expression matrix subset for this feature set.
        
        Returns:
            ExpressionMatrix with only genes in this feature set, or None.
        """
        if self.source_matrix is None:
            return None
        
        return self.source_matrix.subset_by_genes(self.gene_ids)
