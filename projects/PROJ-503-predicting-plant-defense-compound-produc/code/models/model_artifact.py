import pickle
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ModelArtifact:
    """
    Represents a serialized predictive model and its evaluation metrics.
    
    Attributes:
        model: The trained scikit-learn model (e.g., RidgeRegression).
        metrics: Dictionary of evaluation metrics (RMSE, Pearson r, p-value, etc.).
        feature_ids: List of feature IDs used during training.
        target_id: The metabolite this model predicts.
        metadata: Additional metadata (species, cross-validation folds, etc.).
    """
    
    def __init__(
        self,
        model: Optional[Any] = None,
        metrics: Optional[Dict[str, float]] = None,
        feature_ids: Optional[List[str]] = None,
        target_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.model = model
        self.metrics = metrics if metrics is not None else {}
        self.feature_ids = feature_ids if feature_ids is not None else []
        self.target_id = target_id
        self.metadata = metadata if metadata is not None else {}
    
    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Extract feature coefficients if available."""
        if self.model is None:
            return None
        
        if hasattr(self.model, 'coef_'):
            coef = self.model.coef_
            if len(coef) != len(self.feature_ids):
                logger.warning("Coefficient length does not match feature count.")
                return None
            return dict(zip(self.feature_ids, coef.tolist()))
        
        return None
    
    def get_rmse(self) -> Optional[float]:
        """Get RMSE from metrics."""
        return self.metrics.get("rmse")
    
    def get_pearson_r(self) -> Optional[float]:
        """Get Pearson r from metrics."""
        return self.metrics.get("pearson_r")
    
    def get_p_value(self) -> Optional[float]:
        """Get permutation test p-value from metrics."""
        return self.metrics.get("p_value")
    
    def save_pickle(self, filepath: Path) -> None:
        """Save the model artifact to a pickle file."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        
        logger.info(f"ModelArtifact saved to {filepath}")
    
    @classmethod
    def load_pickle(cls, filepath: Path) -> 'ModelArtifact':
        """Load a ModelArtifact from a pickle file."""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"ModelArtifact file not found: {filepath}")
        
        with open(filepath, 'rb') as f:
            return pickle.load(f)
    
    def save_json_metadata(self, filepath: Path) -> None:
        """Save the metrics and metadata to a JSON file (without the model object)."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        metadata_dict = {
            "metrics": self.metrics,
            "feature_ids": self.feature_ids,
            "target_id": self.target_id,
            "metadata": self.metadata
        }
        
        with open(filepath, 'w') as f:
            json.dump(metadata_dict, f, indent=2)
        
        logger.info(f"ModelArtifact metadata saved to {filepath}")
    
    @classmethod
    def load_json_metadata(cls, filepath: Path) -> Dict[str, Any]:
        """Load model metadata from a JSON file."""
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Model metadata file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the artifact to a dictionary (excluding the model object)."""
        return {
            "metrics": self.metrics,
            "feature_ids": self.feature_ids,
            "target_id": self.target_id,
            "metadata": self.metadata
        }
    
    def __repr__(self) -> str:
        return f"ModelArtifact(target={self.target_id}, metrics={len(self.metrics)})"
