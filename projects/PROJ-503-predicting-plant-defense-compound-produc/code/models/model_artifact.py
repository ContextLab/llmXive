"""
ModelArtifact data model class.

Represents a serialized model along with its coefficients and evaluation metrics.
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
    Container for a trained model and its metadata.

    Attributes:
        model: The trained model object (e.g., scikit-learn estimator).
        coefficients (Optional[np.ndarray]): Model coefficients if applicable.
        metrics (Dict[str, Any]): Evaluation metrics (e.g., RMSE, R2, p-values).
        metadata (Dict[str, Any]): Additional metadata (e.g., training date, parameters).
    """

    def __init__(
        self,
        model: Any,
        coefficients: Optional[np.ndarray] = None,
        metrics: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ModelArtifact.

        Args:
            model: The trained model object.
            coefficients: Optional array of coefficients.
            metrics: Dictionary of evaluation metrics.
            metadata: Dictionary of additional metadata.
        """
        self.model = model
        self.coefficients = coefficients
        self.metrics = metrics or {}
        self.metadata = metadata or {}

    def save(self, file_path: str) -> None:
        """
        Save the model artifact to disk.

        The model is pickled, while metrics and metadata are saved as JSON.

        Args:
            file_path: Path to save the artifact (e.g., .pkl).
        """
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        # Save pickled model
        with open(file_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'coefficients': self.coefficients,
                'metrics': self.metrics,
                'metadata': self.metadata
            }, f)

        logger.info(f"Saved ModelArtifact to {file_path}")

    @classmethod
    def load(cls, file_path: str) -> 'ModelArtifact':
        """
        Load a model artifact from disk.

        Args:
            file_path: Path to the pickled artifact.

        Returns:
            ModelArtifact instance.
        """
        logger.info(f"Loading ModelArtifact from {file_path}")
        with open(file_path, 'rb') as f:
            data = pickle.load(f)

        return cls(
            model=data['model'],
            coefficients=data.get('coefficients'),
            metrics=data.get('metrics', {}),
            metadata=data.get('metadata', {})
        )

    def get_metric(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a specific metric.

        Args:
            key: Metric key name.
            default: Default value if key not found.

        Returns:
            Metric value or default.
        """
        return self.metrics.get(key, default)

    def update_metrics(self, new_metrics: Dict[str, Any]) -> None:
        """
        Update metrics with new values.

        Args:
            new_metrics: Dictionary of metrics to update.
        """
        self.metrics.update(new_metrics)

    def __repr__(self) -> str:
        return f"ModelArtifact(metrics={self.metrics}, n_coefficients={len(self.coefficients) if self.coefficients is not None else 0})"
