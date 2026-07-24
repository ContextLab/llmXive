"""
FeatureSet class for handling selected features (genes) for modeling.
"""
import pandas as pd
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

class FeatureSet:
    """
    Represents a set of selected features (genes) with their associated metadata.
    
    Attributes:
        genes (List[str]): List of gene IDs included in the feature set.
        metadata (Dict[str, Any]): Metadata about the selection process (e.g., pathway, method).
        gene_info (Optional[pd.DataFrame]): Detailed info about each gene (e.g., pathway, orthologs).
    """
    
    def __init__(self, genes: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None, 
                 gene_info: Optional[pd.DataFrame] = None):
        self.genes = genes if genes is not None else []
        self.metadata = metadata if metadata is not None else {}
        self.gene_info = gene_info if gene_info is not None else pd.DataFrame()
        
        if self.gene_info.empty and self.genes:
            # Create a basic gene_info dataframe if not provided
            self.gene_info = pd.DataFrame({"gene_id": self.genes})
            self.gene_info.set_index("gene_id", inplace=True)

    def add_gene_info(self, gene_id: str, info: Dict[str, Any]):
        """Add or update information for a specific gene."""
        if gene_id not in self.genes:
            self.genes.append(gene_id)
        
        if gene_id not in self.gene_info.index:
            self.gene_info.loc[gene_id] = info
        else:
            self.gene_info.loc[gene_id, info.keys()] = info.values()
        
        logger.debug(f"Updated info for gene: {gene_id}")

    def filter_by_pathway(self, pathway: str) -> "FeatureSet":
        """
        Filter the feature set to keep only genes associated with a specific pathway.
        
        Args:
            pathway: Pathway name to filter by.
        
        Returns:
            A new FeatureSet instance with filtered genes.
        """
        if "pathway" not in self.gene_info.columns:
            logger.warning("Pathway column not found in gene_info. Returning original set.")
            return self

        filtered_genes = self.gene_info[self.gene_info["pathway"] == pathway].index.tolist()
        filtered_info = self.gene_info.loc[filtered_genes]
        new_metadata = self.metadata.copy()
        new_metadata["filtered_by_pathway"] = pathway
        return FeatureSet(genes=filtered_genes, metadata=new_metadata, gene_info=filtered_info)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the FeatureSet to a dictionary."""
        return {
            "genes": self.genes,
            "metadata": self.metadata,
            "gene_info": self.gene_info.to_dict(orient="index")
        }

    def to_json(self, path: str):
        """Save the FeatureSet to a JSON file."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Saved feature set to {path}")

    @classmethod
    def from_json(cls, path: str) -> "FeatureSet":
        """Load a FeatureSet from a JSON file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Feature set file not found: {path}")
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        gene_info_df = pd.DataFrame.from_dict(data["gene_info"], orient="index")
        if "gene_id" in gene_info_df.columns:
            gene_info_df.set_index("gene_id", inplace=True)
        
        return cls(genes=data["genes"], metadata=data["metadata"], gene_info=gene_info_df)

    def __repr__(self):
        return f"FeatureSet(n_genes={len(self.genes)}, metadata_keys={list(self.metadata.keys())})"
