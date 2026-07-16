"""
FeatureSet class for managing selected features for modeling.

This class represents a subset of features (genes) selected for
predictive modeling, including their associated metadata and
pathway information.
"""

import pandas as pd
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class FeatureSet:
    """
    A class to represent a set of selected features.
    
    Attributes:
        feature_ids (List[str]): List of feature identifiers included in the set.
        feature_info (Dict[str, Any]): Metadata for each feature (e.g., pathway, gene_name).
        source_expression_matrix (Optional[str]): Reference to the source expression matrix.
        selection_method (Optional[str]): Method used for feature selection (e.g., 'KEGG_pathway').
        description (Optional[str]): Description of the feature set.
    """
    
    def __init__(
        self,
        feature_ids: Optional[List[str]] = None,
        feature_info: Optional[Dict[str, Any]] = None,
        source_expression_matrix: Optional[str] = None,
        selection_method: Optional[str] = None,
        description: Optional[str] = None
    ):
        """
        Initialize a FeatureSet instance.
        
        Args:
            feature_ids: List of feature identifiers.
            feature_info: Dictionary mapping feature_id to metadata.
            source_expression_matrix: Identifier of the source expression matrix.
            selection_method: Method used for feature selection.
            description: Description of the feature set.
        """
        self.feature_ids = feature_ids or []
        self.feature_info = feature_info or {}
        self.source_expression_matrix = source_expression_matrix
        self.selection_method = selection_method
        self.description = description
        
        logger.info(f"Initialized FeatureSet with {len(self.feature_ids)} features")
    
    def add_feature(self, feature_id: str, **kwargs) -> None:
        """
        Add a feature to the set.
        
        Args:
            feature_id: The feature identifier.
            **kwargs: Feature metadata key-value pairs.
        """
        if feature_id not in self.feature_ids:
            self.feature_ids.append(feature_id)
        if feature_id not in self.feature_info:
            self.feature_info[feature_id] = {}
        self.feature_info[feature_id].update(kwargs)
    
    def remove_feature(self, feature_id: str) -> bool:
        """
        Remove a feature from the set.
        
        Args:
            feature_id: The feature identifier to remove.
        
        Returns:
            True if the feature was removed, False if not found.
        """
        if feature_id in self.feature_ids:
            self.feature_ids.remove(feature_id)
            if feature_id in self.feature_info:
                del self.feature_info[feature_id]
            return True
        return False
    
    def get_features_by_pathway(self, pathway: str) -> List[str]:
        """
        Get all features belonging to a specific pathway.
        
        Args:
            pathway: The pathway name to filter by.
        
        Returns:
            List of feature IDs in the pathway.
        """
        return [
            fid for fid in self.feature_ids
            if self.feature_info.get(fid, {}).get('pathway') == pathway
        ]
    
    def get_features_by_species(self, species: str) -> List[str]:
        """
        Get all features belonging to a specific species.
        
        Args:
            species: The species name to filter by.
        
        Returns:
            List of feature IDs in the species.
        """
        return [
            fid for fid in self.feature_ids
            if self.feature_info.get(fid, {}).get('species') == species
        ]
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the feature set to a DataFrame.
        
        Returns:
            DataFrame with feature metadata.
        """
        rows = []
        for fid in self.feature_ids:
            row = {'feature_id': fid}
            row.update(self.feature_info.get(fid, {}))
            rows.append(row)
        return pd.DataFrame(rows)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the feature set to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the feature set.
        """
        return {
            'feature_ids': self.feature_ids,
            'feature_info': self.feature_info,
            'source_expression_matrix': self.source_expression_matrix,
            'selection_method': self.selection_method,
            'description': self.description
        }
    
    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> 'FeatureSet':
        """
        Create a FeatureSet from a dictionary.
        
        Args:
            data_dict: Dictionary representation of the feature set.
        
        Returns:
            FeatureSet instance.
        """
        return cls(
            feature_ids=data_dict.get('feature_ids', []),
            feature_info=data_dict.get('feature_info', {}),
            source_expression_matrix=data_dict.get('source_expression_matrix'),
            selection_method=data_dict.get('selection_method'),
            description=data_dict.get('description')
        )
    
    def save_json(self, filepath: Path) -> None:
        """
        Save the feature set to a JSON file.
        
        Args:
            filepath: Path to the output file.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Saved FeatureSet to {filepath}")
    
    @classmethod
    def load_json(cls, filepath: Path) -> 'FeatureSet':
        """
        Load a FeatureSet from a JSON file.
        
        Args:
            filepath: Path to the input file.
        
        Returns:
            FeatureSet instance.
        """
        filepath = Path(filepath)
        with open(filepath, 'r') as f:
            data_dict = json.load(f)
        return cls.from_dict(data_dict)
    
    def save_csv(self, filepath: Path) -> None:
        """
        Save the feature set to a CSV file.
        
        Args:
            filepath: Path to the output file.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        df = self.to_dataframe()
        df.to_csv(filepath, index=False)
        logger.info(f"Saved FeatureSet to {filepath}")
    
    @classmethod
    def load_csv(
        cls,
        filepath: Path,
        source_expression_matrix: Optional[str] = None,
        selection_method: Optional[str] = None,
        description: Optional[str] = None
    ) -> 'FeatureSet':
        """
        Load a FeatureSet from a CSV file.
        
        Args:
            filepath: Path to the input file.
            source_expression_matrix: Optional source identifier.
            selection_method: Optional selection method.
            description: Optional description.
        
        Returns:
            FeatureSet instance.
        """
        filepath = Path(filepath)
        df = pd.read_csv(filepath)
        
        feature_ids = df['feature_id'].tolist()
        feature_info = {}
        
        for _, row in df.iterrows():
            fid = row['feature_id']
            feature_info[fid] = row.to_dict()
            # Remove the feature_id from the metadata dict as it's the key
            feature_info[fid].pop('feature_id', None)
        
        return cls(
            feature_ids=feature_ids,
            feature_info=feature_info,
            source_expression_matrix=source_expression_matrix,
            selection_method=selection_method,
            description=description
        )
    
    def __len__(self) -> int:
        return len(self.feature_ids)
    
    def __contains__(self, feature_id: str) -> bool:
        return feature_id in self.feature_ids
    
    def __repr__(self) -> str:
        return (
            f"FeatureSet(features={len(self.feature_ids)}, "
            f"method={self.selection_method or 'unknown'})"
        )
