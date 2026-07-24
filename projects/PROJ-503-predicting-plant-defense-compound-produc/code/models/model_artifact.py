"""
ModelArtifact class for storing trained model information and metrics.
"""
import pickle
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
import numpy as np
import logging

logger = logging.getLogger(__name__)

class ModelArtifact:
    """
    Represents a serialized model artifact including coefficients, metrics, and metadata.
    
    Attributes:
        model (Any): The trained model object (e.g., Ridge regression).
        coefficients (np.ndarray): Model coefficients.
        metrics (Dict[str, Any]): Evaluation metrics (RMSE, Pearson r, p-values).
        metadata (Dict[str, Any]): Additional metadata (e.g., training parameters).
    """
    
    def __init__(self, model: Optional[Any] = None, coefficients: Optional[np.ndarray] = None, 
                 metrics: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None):
        self.model = model
        self.coefficients = coefficients
        self.metrics = metrics if metrics is not None else {}
        self.metadata = metadata if metadata is not None else {}

    def add_metric(self, key: str, value: Any):
        """Add or update an evaluation metric."""
        self.metrics[key] = value
        logger.debug(f"Added metric: {key} = {value}")

    def add_metadata(self, key: str, value: Any):
        """Add or update a metadata field."""
        self.metadata[key] = value
        logger.debug(f"Added metadata: {key} = {value}")

    def save(self, path: str):
        """
        Save the model artifact to disk.
        
        Args:
            path: Directory path where the artifact will be saved.
        
        The model object is pickled, while coefficients, metrics, and metadata are saved as JSON.
        """
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save pickled model
        model_path = Path(path) / "model.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        # Save JSON components
        json_data = {
            "coefficients": self.coefficients.tolist() if self.coefficients is not None else None,
            "metrics": self.metrics,
            "metadata": self.metadata
        }
        json_path = Path(path) / "model_artifact.json"
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        logger.info(f"Saved model artifact to {path}")

    @classmethod
    def load(cls, path: str) -> "ModelArtifact":
        """
        Load a model artifact from disk.
        
        Args:
            path: Directory path where the artifact is stored.
        
        Returns:
            Loaded ModelArtifact instance.
        """
        path = Path(path)
        model_path = path / "model.pkl"
        json_path = path / "model_artifact.json"
        
        if not model_path.exists() or not json_path.exists():
            raise FileNotFoundError(f"Model artifact files not found in {path}")
        
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        with open(json_path, 'r') as f:
            json_data = json.load(f)
        
        coefficients = np.array(json_data["coefficients"]) if json_data["coefficients"] is not None else None
        
        return cls(
            model=model,
            coefficients=coefficients,
            metrics=json_data["metrics"],
            metadata=json_data["metadata"]
        )

    def __repr__(self):
        return f"ModelArtifact(metrics={list(self.metrics.keys())}, metadata_keys={list(self.metadata.keys())})"