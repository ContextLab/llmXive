"""
ExpressionMatrix class for managing gene expression data.

This class handles the storage, validation, and I/O operations for
gene expression matrices (samples x genes) typically derived from
transcriptomic data (RNA-seq, microarrays).
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
    A class to represent a gene expression matrix.
    
    Attributes:
        data (pd.DataFrame): Expression values with samples as rows and genes as columns.
        metadata (Dict[str, Any]): Sample-level metadata (e.g., treatment, species, batch).
        gene_info (Dict[str, Any]): Gene-level metadata (e.g., gene_id, gene_name, pathway).
        source (str): Data source identifier (e.g., GEO accession).
        normalized (bool): Whether the data has been normalized.
        normalization_method (Optional[str]): Method used for normalization (e.g., 'TPM', 'FPKM', 'Z-score').
    """
    
    def __init__(
        self,
        data: Optional[pd.DataFrame] = None,
        metadata: Optional[Dict[str, Any]] = None,
        gene_info: Optional[Dict[str, Any]] = None,
        source: str = "unknown",
        normalized: bool = False,
        normalization_method: Optional[str] = None
    ):
        """
        Initialize an ExpressionMatrix instance.
        
        Args:
            data: DataFrame with samples as rows, genes as columns.
            metadata: Dictionary of sample metadata.
            gene_info: Dictionary of gene metadata.
            source: Source identifier for the data.
            normalized: Flag indicating if data is normalized.
            normalization_method: Name of the normalization method used.
        """
        if data is not None:
            if not isinstance(data, pd.DataFrame):
                raise TypeError("data must be a pandas DataFrame")
            self.data = data
        else:
            self.data = pd.DataFrame()
        
        self.metadata = metadata or {}
        self.gene_info = gene_info or {}
        self.source = source
        self.normalized = normalized
        self.normalization_method = normalization_method
        
        logger.info(f"Initialized ExpressionMatrix with {len(self.data)} samples and {len(self.data.columns)} genes")
    
    def add_sample_metadata(self, sample_id: str, **kwargs) -> None:
        """
        Add or update metadata for a specific sample.
        
        Args:
            sample_id: The sample identifier.
            **kwargs: Metadata key-value pairs.
        """
        if sample_id not in self.metadata:
            self.metadata[sample_id] = {}
        self.metadata[sample_id].update(kwargs)
    
    def add_gene_metadata(self, gene_id: str, **kwargs) -> None:
        """
        Add or update metadata for a specific gene.
        
        Args:
            gene_id: The gene identifier.
            **kwargs: Metadata key-value pairs.
        """
        if gene_id not in self.gene_info:
            self.gene_info[gene_id] = {}
        self.gene_info[gene_id].update(kwargs)
    
    def filter_samples(self, condition: callable) -> 'ExpressionMatrix':
        """
        Filter samples based on a condition function.
        
        Args:
            condition: A function that takes a sample_id and returns True to keep.
        
        Returns:
            A new ExpressionMatrix with filtered samples.
        """
        filtered_samples = [sid for sid in self.data.index if condition(sid)]
        new_data = self.data.loc[filtered_samples]
        new_metadata = {k: v for k, v in self.metadata.items() if k in filtered_samples}
        
        return ExpressionMatrix(
            data=new_data,
            metadata=new_metadata,
            gene_info=self.gene_info,
            source=self.source,
            normalized=self.normalized,
            normalization_method=self.normalization_method
        )
    
    def filter_genes(self, condition: callable) -> 'ExpressionMatrix':
        """
        Filter genes based on a condition function.
        
        Args:
            condition: A function that takes a gene_id and returns True to keep.
        
        Returns:
            A new ExpressionMatrix with filtered genes.
        """
        filtered_genes = [gid for gid in self.data.columns if condition(gid)]
        new_data = self.data.loc[:, filtered_genes]
        new_gene_info = {k: v for k, v in self.gene_info.items() if k in filtered_genes}
        
        return ExpressionMatrix(
            data=new_data,
            metadata=self.metadata,
            gene_info=new_gene_info,
            source=self.source,
            normalized=self.normalized,
            normalization_method=self.normalization_method
        )
    
    def get_sample_ids(self) -> List[str]:
        """Return list of sample identifiers."""
        return list(self.data.index)
    
    def get_gene_ids(self) -> List[str]:
        """Return list of gene identifiers."""
        return list(self.data.columns)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the matrix to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the matrix.
        """
        return {
            'data': self.data.to_dict(orient='split'),
            'metadata': self.metadata,
            'gene_info': self.gene_info,
            'source': self.source,
            'normalized': self.normalized,
            'normalization_method': self.normalization_method
        }
    
    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> 'ExpressionMatrix':
        """
        Create an ExpressionMatrix from a dictionary.
        
        Args:
            data_dict: Dictionary representation of the matrix.
        
        Returns:
            ExpressionMatrix instance.
        """
        data = pd.DataFrame(
            data_dict['data']['data'],
            index=data_dict['data']['index'],
            columns=data_dict['data']['columns']
        )
        return cls(
            data=data,
            metadata=data_dict.get('metadata', {}),
            gene_info=data_dict.get('gene_info', {}),
            source=data_dict.get('source', 'unknown'),
            normalized=data_dict.get('normalized', False),
            normalization_method=data_dict.get('normalization_method')
        )
    
    def save_json(self, filepath: Path) -> None:
        """
        Save the matrix to a JSON file.
        
        Args:
            filepath: Path to the output file.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, default=str)
        logger.info(f"Saved ExpressionMatrix to {filepath}")
    
    @classmethod
    def load_json(cls, filepath: Path) -> 'ExpressionMatrix':
        """
        Load an ExpressionMatrix from a JSON file.
        
        Args:
            filepath: Path to the input file.
        
        Returns:
            ExpressionMatrix instance.
        """
        filepath = Path(filepath)
        with open(filepath, 'r') as f:
            data_dict = json.load(f)
        return cls.from_dict(data_dict)
    
    def save_csv(self, filepath: Path, metadata_filepath: Optional[Path] = None) -> None:
        """
        Save the expression matrix to CSV files.
        
        Args:
            filepath: Path to the main expression CSV file.
            metadata_filepath: Optional path for metadata CSV file.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        self.data.to_csv(filepath)
        logger.info(f"Saved expression data to {filepath}")
        
        if metadata_filepath:
            metadata_filepath = Path(metadata_filepath)
            metadata_filepath.parent.mkdir(parents=True, exist_ok=True)
            metadata_df = pd.DataFrame(self.metadata).T
            metadata_df.to_csv(metadata_filepath)
            logger.info(f"Saved metadata to {metadata_filepath}")
    
    @classmethod
    def load_csv(
        cls,
        filepath: Path,
        metadata_filepath: Optional[Path] = None,
        gene_info_filepath: Optional[Path] = None
    ) -> 'ExpressionMatrix':
        """
        Load an ExpressionMatrix from CSV files.
        
        Args:
            filepath: Path to the main expression CSV file.
            metadata_filepath: Optional path for metadata CSV file.
            gene_info_filepath: Optional path for gene info CSV file.
        
        Returns:
            ExpressionMatrix instance.
        """
        filepath = Path(filepath)
        data = pd.read_csv(filepath, index_col=0)
        
        metadata = {}
        if metadata_filepath and Path(metadata_filepath).exists():
            metadata_df = pd.read_csv(metadata_filepath, index_col=0)
            metadata = metadata_df.to_dict(orient='index')
        
        gene_info = {}
        if gene_info_filepath and Path(gene_info_filepath).exists():
            gene_info_df = pd.read_csv(gene_info_filepath, index_col=0)
            gene_info = gene_info_df.to_dict(orient='index')
        
        return cls(
            data=data,
            metadata=metadata,
            gene_info=gene_info,
            source="csv_load"
        )
    
    def __repr__(self) -> str:
        return (
            f"ExpressionMatrix(samples={len(self.data)}, genes={len(self.data.columns)}, "
            f"source={self.source}, normalized={self.normalized})"
        )
