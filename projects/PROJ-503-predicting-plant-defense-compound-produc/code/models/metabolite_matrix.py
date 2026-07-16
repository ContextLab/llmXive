"""
MetaboliteMatrix class for managing metabolite concentration data.

This class handles the storage, validation, and I/O operations for
metabolite concentration matrices (samples x metabolites) derived from
metabolomics experiments.
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
    A class to represent a metabolite concentration matrix.
    
    Attributes:
        data (pd.DataFrame): Concentration values with samples as rows and metabolites as columns.
        metadata (Dict[str, Any]): Sample-level metadata.
        metabolite_info (Dict[str, Any]): Metabolite-level metadata (e.g., compound_id, name, class).
        source (str): Data source identifier.
        normalized (bool): Whether the data has been normalized.
        normalization_method (Optional[str]): Method used for normalization.
        log_transformed (bool): Whether the data has been log-transformed.
    """
    
    def __init__(
        self,
        data: Optional[pd.DataFrame] = None,
        metadata: Optional[Dict[str, Any]] = None,
        metabolite_info: Optional[Dict[str, Any]] = None,
        source: str = "unknown",
        normalized: bool = False,
        normalization_method: Optional[str] = None,
        log_transformed: bool = False
    ):
        """
        Initialize a MetaboliteMatrix instance.
        
        Args:
            data: DataFrame with samples as rows, metabolites as columns.
            metadata: Dictionary of sample metadata.
            metabolite_info: Dictionary of metabolite metadata.
            source: Source identifier for the data.
            normalized: Flag indicating if data is normalized.
            normalization_method: Name of the normalization method used.
            log_transformed: Flag indicating if data is log-transformed.
        """
        if data is not None:
            if not isinstance(data, pd.DataFrame):
                raise TypeError("data must be a pandas DataFrame")
            self.data = data
        else:
            self.data = pd.DataFrame()
        
        self.metadata = metadata or {}
        self.metabolite_info = metabolite_info or {}
        self.source = source
        self.normalized = normalized
        self.normalization_method = normalization_method
        self.log_transformed = log_transformed
        
        logger.info(f"Initialized MetaboliteMatrix with {len(self.data)} samples and {len(self.data.columns)} metabolites")
    
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
    
    def add_metabolite_metadata(self, metabolite_id: str, **kwargs) -> None:
        """
        Add or update metadata for a specific metabolite.
        
        Args:
            metabolite_id: The metabolite identifier.
            **kwargs: Metadata key-value pairs.
        """
        if metabolite_id not in self.metabolite_info:
            self.metabolite_info[metabolite_id] = {}
        self.metabolite_info[metabolite_id].update(kwargs)
    
    def filter_samples(self, condition: callable) -> 'MetaboliteMatrix':
        """
        Filter samples based on a condition function.
        
        Args:
            condition: A function that takes a sample_id and returns True to keep.
        
        Returns:
            A new MetaboliteMatrix with filtered samples.
        """
        filtered_samples = [sid for sid in self.data.index if condition(sid)]
        new_data = self.data.loc[filtered_samples]
        new_metadata = {k: v for k, v in self.metadata.items() if k in filtered_samples}
        
        return MetaboliteMatrix(
            data=new_data,
            metadata=new_metadata,
            metabolite_info=self.metabolite_info,
            source=self.source,
            normalized=self.normalized,
            normalization_method=self.normalization_method,
            log_transformed=self.log_transformed
        )
    
    def filter_metabolites(self, condition: callable) -> 'MetaboliteMatrix':
        """
        Filter metabolites based on a condition function.
        
        Args:
            condition: A function that takes a metabolite_id and returns True to keep.
        
        Returns:
            A new MetaboliteMatrix with filtered metabolites.
        """
        filtered_metabolites = [mid for mid in self.data.columns if condition(mid)]
        new_data = self.data.loc[:, filtered_metabolites]
        new_metabolite_info = {k: v for k, v in self.metabolite_info.items() if k in filtered_metabolites}
        
        return MetaboliteMatrix(
            data=new_data,
            metadata=self.metadata,
            metabolite_info=new_metabolite_info,
            source=self.source,
            normalized=self.normalized,
            normalization_method=self.normalization_method,
            log_transformed=self.log_transformed
        )
    
    def get_sample_ids(self) -> List[str]:
        """Return list of sample identifiers."""
        return list(self.data.index)
    
    def get_metabolite_ids(self) -> List[str]:
        """Return list of metabolite identifiers."""
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
            'metabolite_info': self.metabolite_info,
            'source': self.source,
            'normalized': self.normalized,
            'normalization_method': self.normalization_method,
            'log_transformed': self.log_transformed
        }
    
    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> 'MetaboliteMatrix':
        """
        Create a MetaboliteMatrix from a dictionary.
        
        Args:
            data_dict: Dictionary representation of the matrix.
        
        Returns:
            MetaboliteMatrix instance.
        """
        data = pd.DataFrame(
            data_dict['data']['data'],
            index=data_dict['data']['index'],
            columns=data_dict['data']['columns']
        )
        return cls(
            data=data,
            metadata=data_dict.get('metadata', {}),
            metabolite_info=data_dict.get('metabolite_info', {}),
            source=data_dict.get('source', 'unknown'),
            normalized=data_dict.get('normalized', False),
            normalization_method=data_dict.get('normalization_method'),
            log_transformed=data_dict.get('log_transformed', False)
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
        logger.info(f"Saved MetaboliteMatrix to {filepath}")
    
    @classmethod
    def load_json(cls, filepath: Path) -> 'MetaboliteMatrix':
        """
        Load a MetaboliteMatrix from a JSON file.
        
        Args:
            filepath: Path to the input file.
        
        Returns:
            MetaboliteMatrix instance.
        """
        filepath = Path(filepath)
        with open(filepath, 'r') as f:
            data_dict = json.load(f)
        return cls.from_dict(data_dict)
    
    def save_csv(self, filepath: Path, metadata_filepath: Optional[Path] = None) -> None:
        """
        Save the metabolite matrix to CSV files.
        
        Args:
            filepath: Path to the main metabolite CSV file.
            metadata_filepath: Optional path for metadata CSV file.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        self.data.to_csv(filepath)
        logger.info(f"Saved metabolite data to {filepath}")
        
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
        metabolite_info_filepath: Optional[Path] = None
    ) -> 'MetaboliteMatrix':
        """
        Load a MetaboliteMatrix from CSV files.
        
        Args:
            filepath: Path to the main metabolite CSV file.
            metadata_filepath: Optional path for metadata CSV file.
            metabolite_info_filepath: Optional path for metabolite info CSV file.
        
        Returns:
            MetaboliteMatrix instance.
        """
        filepath = Path(filepath)
        data = pd.read_csv(filepath, index_col=0)
        
        metadata = {}
        if metadata_filepath and Path(metadata_filepath).exists():
            metadata_df = pd.read_csv(metadata_filepath, index_col=0)
            metadata = metadata_df.to_dict(orient='index')
        
        metabolite_info = {}
        if metabolite_info_filepath and Path(metabolite_info_filepath).exists():
            metabolite_info_df = pd.read_csv(metabolite_info_filepath, index_col=0)
            metabolite_info = metabolite_info_df.to_dict(orient='index')
        
        return cls(
            data=data,
            metadata=metadata,
            metabolite_info=metabolite_info,
            source="csv_load"
        )
    
    def __repr__(self) -> str:
        return (
            f"MetaboliteMatrix(samples={len(self.data)}, metabolites={len(self.data.columns)}, "
            f"source={self.source}, log_transformed={self.log_transformed})"
        )
