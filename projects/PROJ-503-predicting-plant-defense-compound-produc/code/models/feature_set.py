import pandas as pd
from typing import Optional, List, Dict, Any
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class FeatureSet:
    """
    Represents a filtered set of features (genes) selected for modeling.
    This typically results from pathway filtering and zero-variance removal.
    
    Attributes:
        data: DataFrame containing the selected feature expression values.
        feature_info: Dictionary mapping feature IDs to metadata (e.g., KEGG pathway).
        source_matrix_id: Identifier of the source ExpressionMatrix.
    """
    
    def __init__(
        self,
        data: Optional[pd.DataFrame] = None,
        feature_info: Optional[Dict[str, Dict[str, Any]]] = None,
        source_matrix_id: Optional[str] = None
    ):
        self.data = data if data is not None else pd.DataFrame()
        self.feature_info = feature_info if feature_info is not None else {}
        self.source_matrix_id = source_matrix_id
        
        if not self.data.empty:
            self._validate_features()
    
    def _validate_features(self):
        """Ensure features are valid."""
        if self.data.empty:
            raise ValueError("FeatureSet data cannot be empty.")
        
        if len(self.data.columns) == 0:
            raise ValueError("FeatureSet must have at least one sample column.")
    
    def get_feature_ids(self) -> List[str]:
        """Return list of feature identifiers (index)."""
        return list(self.data.index)
    
    def get_sample_ids(self) -> List[str]:
        """Return list of sample identifiers (columns)."""
        return list(self.data.columns)
    
    def get_dimensions(self) -> tuple:
        """Return (n_features, n_samples)."""
        return self.data.shape
    
    def get_pathway_info(self, feature_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific feature."""
        return self.feature_info.get(feature_id)
    
    def filter_samples(self, sample_ids: List[str]) -> 'FeatureSet':
        """Return a new FeatureSet filtered to only include specified samples."""
        available = set(self.data.columns)
        requested = set(sample_ids)
        missing = requested - available
        
        if missing:
            logger.warning(f"Samples not found in FeatureSet: {len(missing)}")
        
        filtered_data = self.data[list(available.intersection(requested))]
        return FeatureSet(
            data=filtered_data,
            feature_info=self.feature_info.copy(),
            source_matrix_id=self.source_matrix_id
        )
    
    def to_csv(self, filepath: Path) -> None:
        """Save the feature set matrix to a CSV file."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        self.data.to_csv(filepath)
        logger.info(f"FeatureSet saved to {filepath}")
    
    @classmethod
    def from_csv(cls, filepath: Path) -> 'FeatureSet':
        """Load a FeatureSet from a CSV file."""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"FeatureSet file not found: {filepath}")
        
        data = pd.read_csv(filepath, index_col=0)
        return cls(data=data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the FeatureSet to a dictionary representation."""
        return {
            "data": self.data.to_dict(orient="split"),
            "feature_info": self.feature_info,
            "source_matrix_id": self.source_matrix_id
        }
    
    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> 'FeatureSet':
        """Reconstruct a FeatureSet from a dictionary."""
        data = pd.DataFrame(
            data_dict["data"]["data"],
            index=data_dict["data"]["index"],
            columns=data_dict["data"]["columns"]
        )
        return cls(
            data=data,
            feature_info=data_dict.get("feature_info", {}),
            source_matrix_id=data_dict.get("source_matrix_id")
        )
    
    def __repr__(self) -> str:
        n_features, n_samples = self.get_dimensions()
        return f"FeatureSet(features={n_features}, samples={n_samples})"
