"""
ModelArtifact class for managing trained model artifacts.

This class handles the storage, validation, and I/O operations for
trained predictive models including coefficients, metrics, and
training metadata.
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
    A class to represent a trained model artifact.
    
    Attributes:
        model (Any): The trained model object (e.g., RidgeRegression).
        coefficients (Optional[np.ndarray]): Model coefficients.
        intercept (Optional[float]): Model intercept.
        metrics (Dict[str, Any]): Evaluation metrics (e.g., RMSE, R2, p-value).
        feature_names (Optional[List[str]]): Names of features used in training.
        target_name (Optional[str]): Name of the target variable.
        training_metadata (Dict[str, Any]): Metadata about the training process.
    """
    
    def __init__(
        self,
        model: Optional[Any] = None,
        coefficients: Optional[np.ndarray] = None,
        intercept: Optional[float] = None,
        metrics: Optional[Dict[str, Any]] = None,
        feature_names: Optional[List[str]] = None,
        target_name: Optional[str] = None,
        training_metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a ModelArtifact instance.
        
        Args:
            model: The trained model object.
            coefficients: Model coefficients array.
            intercept: Model intercept value.
            metrics: Dictionary of evaluation metrics.
            feature_names: List of feature names used in training.
            target_name: Name of the target variable.
            training_metadata: Metadata about the training process.
        """
        self.model = model
        self.coefficients = coefficients
        self.intercept = intercept
        self.metrics = metrics or {}
        self.feature_names = feature_names or []
        self.target_name = target_name
        self.training_metadata = training_metadata or {}
        
        logger.info(f"Initialized ModelArtifact for target '{target_name}' with {len(feature_names or [])} features")
    
    def add_metric(self, name: str, value: float) -> None:
        """
        Add or update a metric.
        
        Args:
            name: Metric name.
            value: Metric value.
        """
        self.metrics[name] = value
    
    def add_training_metadata(self, **kwargs) -> None:
        """
        Add training metadata.
        
        Args:
            **kwargs: Metadata key-value pairs.
        """
        self.training_metadata.update(kwargs)
    
    def get_coefficients_dict(self) -> Dict[str, float]:
        """
        Get coefficients as a dictionary mapping feature names to values.
        
        Returns:
            Dictionary of coefficients.
        """
        if self.coefficients is None or self.feature_names is None:
            return {}
        return dict(zip(self.feature_names, self.coefficients.tolist()))
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the artifact to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the artifact.
        """
        # Convert numpy arrays to lists for JSON serialization
        coeffs = self.coefficients.tolist() if self.coefficients is not None else None
        
        return {
            'coefficients': coeffs,
            'intercept': self.intercept,
            'metrics': self.metrics,
            'feature_names': self.feature_names,
            'target_name': self.target_name,
            'training_metadata': self.training_metadata
        }
    
    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]) -> 'ModelArtifact':
        """
        Create a ModelArtifact from a dictionary.
        
        Args:
            data_dict: Dictionary representation of the artifact.
        
        Returns:
            ModelArtifact instance.
        """
        # Convert lists back to numpy arrays
        coeffs = np.array(data_dict['coefficients']) if data_dict.get('coefficients') is not None else None
        
        return cls(
            coefficients=coeffs,
            intercept=data_dict.get('intercept'),
            metrics=data_dict.get('metrics', {}),
            feature_names=data_dict.get('feature_names', []),
            target_name=data_dict.get('target_name'),
            training_metadata=data_dict.get('training_metadata', {})
        )
    
    def save_pickle(self, filepath: Path) -> None:
        """
        Save the model artifact (including the model object) to a pickle file.
        
        Args:
            filepath: Path to the output file.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        logger.info(f"Saved ModelArtifact to {filepath}")
    
    @classmethod
    def load_pickle(cls, filepath: Path) -> 'ModelArtifact':
        """
        Load a ModelArtifact from a pickle file.
        
        Args:
            filepath: Path to the input file.
        
        Returns:
            ModelArtifact instance.
        """
        filepath = Path(filepath)
        with open(filepath, 'rb') as f:
            artifact = pickle.load(f)
        logger.info(f"Loaded ModelArtifact from {filepath}")
        return artifact
    
    def save_json(self, filepath: Path) -> None:
        """
        Save the artifact metadata (excluding the model object) to a JSON file.
        
        Args:
            filepath: Path to the output file.
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
        logger.info(f"Saved ModelArtifact metadata to {filepath}")
    
    @classmethod
    def load_json(cls, filepath: Path) -> 'ModelArtifact':
        """
        Load a ModelArtifact from a JSON file (metadata only, no model object).
        
        Args:
            filepath: Path to the input file.
        
        Returns:
            ModelArtifact instance.
        """
        filepath = Path(filepath)
        with open(filepath, 'r') as f:
            data_dict = json.load(f)
        return cls.from_dict(data_dict)
    
    def __repr__(self) -> str:
        return (
            f"ModelArtifact(target={self.target_name}, features={len(self.feature_names)}, "
            f"metrics={list(self.metrics.keys())})"
        )