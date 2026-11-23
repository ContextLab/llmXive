"""
ModelArtifact data model.

Represents a trained model with its coefficients, evaluation metrics,
and metadata for reproducibility.

Attributes:
    model_type: Type of model (e.g., 'RidgeRegression')
    coefficients: Dict mapping gene_id to coefficient value
    metrics: Dict of evaluation metrics (RMSE, Pearson r, etc.)
    hyperparameters: Dict of model hyperparameters
    training_metadata: Dict of additional training information
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
    Data model for storing trained model artifacts.
    """
    
    def __init__(
        self,
        model_type: str,
        coefficients: Dict[str, float],
        metrics: Dict[str, float],
        hyperparameters: Optional[Dict[str, Any]] = None,
        training_metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a ModelArtifact.
        
        Args:
            model_type: Type of model (e.g., 'RidgeRegression').
            coefficients: Dict mapping feature_id to coefficient value.
            metrics: Dict of evaluation metrics (RMSE, Pearson r, etc.).
            hyperparameters: Dict of model hyperparameters.
            training_metadata: Dict of additional training information.
        """
        self.model_type = model_type
        self.coefficients = coefficients
        self.metrics = metrics
        self.hyperparameters = hyperparameters or {}
        self.training_metadata = training_metadata or {}
        
        logger.info(f"Created ModelArtifact for {model_type} with {len(coefficients)} coefficients")

    def to_pickle(self, filepath: str) -> None:
        """
        Save the model artifact to a pickle file.
        
        Args:
            filepath: Path to output pickle file.
        """
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        logger.info(f"Saved ModelArtifact to {filepath}")

    @classmethod
    def from_pickle(cls, filepath: str) -> 'ModelArtifact':
        """
        Load a ModelArtifact from a pickle file.
        
        Args:
            filepath: Path to input pickle file.
        
        Returns:
            ModelArtifact instance.
        
        Raises:
            FileNotFoundError: If file doesn't exist.
        """
        if not Path(filepath).exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'rb') as f:
            return pickle.load(f)

    def to_json(self, filepath: str) -> None:
        """
        Save the model artifact metadata to a JSON file.
        
        Note: Coefficients are saved as a list of [gene_id, coefficient] pairs
        to preserve order and handle potential float precision.
        
        Args:
            filepath: Path to output JSON file.
        """
        data = {
            'model_type': self.model_type,
            'coefficients': [[k, v] for k, v in self.coefficients.items()],
            'metrics': self.metrics,
            'hyperparameters': self.hyperparameters,
            'training_metadata': self.training_metadata
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved ModelArtifact metadata to {filepath}")

    @classmethod
    def from_json(cls, filepath: str) -> 'ModelArtifact':
        """
        Load a ModelArtifact from a JSON file.
        
        Args:
            filepath: Path to input JSON file.
        
        Returns:
            ModelArtifact instance.
        
        Raises:
            FileNotFoundError: If file doesn't exist.
        """
        if not Path(filepath).exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Reconstruct coefficients dict
        coefficients = {k: float(v) for k, v in data['coefficients']}
        
        return cls(
            model_type=data['model_type'],
            coefficients=coefficients,
            metrics=data['metrics'],
            hyperparameters=data.get('hyperparameters', {}),
            training_metadata=data.get('training_metadata', {})
        )

    def get_coefficients(self) -> Dict[str, float]:
        """Return the coefficients dictionary."""
        return self.coefficients.copy()

    def get_metrics(self) -> Dict[str, float]:
        """Return the metrics dictionary."""
        return self.metrics.copy()

    def get_top_coefficients(self, n: int = 10) -> List[tuple]:
        """
        Get the top n genes by absolute coefficient value.
        
        Args:
            n: Number of top coefficients to return.
        
        Returns:
            List of (gene_id, coefficient) tuples sorted by absolute value.
        """
        sorted_coeffs = sorted(
            self.coefficients.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        return sorted_coeffs[:n]

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get normalized feature importance (absolute coefficient values).
        
        Returns:
            Dict mapping gene_id to normalized importance score.
        """
        abs_coeffs = {k: abs(v) for k, v in self.coefficients.items()}
        total = sum(abs_coeffs.values())
        
        if total == 0:
            return {k: 0.0 for k in abs_coeffs}
        
        return {k: v / total for k, v in abs_coeffs.items()}