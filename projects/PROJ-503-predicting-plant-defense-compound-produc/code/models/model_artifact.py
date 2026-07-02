"""
ModelArtifact data model for serialized machine learning models and metrics.

Stores model coefficients, evaluation metrics, and training metadata.
"""
import pickle
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
import numpy as np

class ModelArtifact:
    """
    Container for a trained model and its associated metadata.
    
    Attributes:
        model: The trained model object (e.g., sklearn Ridge).
        coefficients: Dictionary or array of feature coefficients.
        metrics: Dictionary of evaluation metrics (e.g., RMSE, R2, p-value).
        metadata: Dictionary of training metadata (e.g., train_date, parameters).
    """
    
    def __init__(
        self,
        model: Optional[Any] = None,
        coefficients: Optional[Any] = None,
        metrics: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a ModelArtifact.
        
        Args:
            model: The trained model object.
            coefficients: Model coefficients (array or dict).
            metrics: Dictionary of evaluation metrics.
            metadata: Dictionary of training metadata.
        """
        self.model = model
        self.coefficients = coefficients
        self.metrics = metrics or {}
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation (excluding the raw model object).
        
        Returns:
            Dictionary with serializable fields.
        """
        return {
            "coefficients": (
                self.coefficients.tolist() 
                if isinstance(self.coefficients, np.ndarray) 
                else self.coefficients
            ),
            "metrics": self.metrics,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> "ModelArtifact":
        """
        Create a ModelArtifact from a dictionary.
        
        Note: This reconstructs metadata and metrics, but not the raw model object.
        The model must be reloaded separately or the artifact is metadata-only.
        
        Args:
            data_dict: Dictionary containing 'coefficients', 'metrics', 'metadata'.
        
        Returns:
            New ModelArtifact instance (with model=None).
        """
        coeffs = data_dict.get("coefficients")
        if isinstance(coeffs, list):
            coeffs = np.array(coeffs)
        
        return cls(
            model=None,
            coefficients=coeffs,
            metrics=data_dict.get("metrics", {}),
            metadata=data_dict.get("metadata", {}),
        )

    def save(self, path: Path) -> None:
        """
        Save the artifact to disk: model as pickle, metadata/metrics as JSON.
        
        Args:
            path: Path to the output directory or base filename.
        """
        path = Path(path)
        if path.suffix:
            base_path = path.parent
            pkl_path = path
            json_path = path.with_suffix(".json")
        else:
            base_path = path.parent
            pkl_path = path / "model.pkl"
            json_path = path / "model_metadata.json"
        
        # Save model object
        with open(pkl_path, "wb") as f:
            pickle.dump(self.model, f)
        
        # Save metadata and metrics
        with open(json_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> "ModelArtifact":
        """
        Load an artifact from disk.
        
        Args:
            path: Path to the pickle file or directory containing model.pkl and model_metadata.json.
        
        Returns:
            Loaded ModelArtifact instance.
        """
        path = Path(path)
        if path.suffix == ".pkl":
            pkl_path = path
            json_path = path.with_suffix(".json")
        else:
            pkl_path = path / "model.pkl"
            json_path = path / "model_metadata.json"
        
        with open(pkl_path, "rb") as f:
            model = pickle.load(f)
        
        with open(json_path, "r") as f:
            data_dict = json.load(f)
        
        artifact = cls.from_dict(data_dict)
        artifact.model = model
        return artifact

    def get_coefficients(self) -> Any:
        """Return coefficients, ensuring they are in a usable format."""
        return self.coefficients

    def get_metrics(self) -> Dict[str, float]:
        """Return evaluation metrics."""
        return self.metrics

    def get_metadata(self) -> Dict[str, Any]:
        """Return training metadata."""
        return self.metadata