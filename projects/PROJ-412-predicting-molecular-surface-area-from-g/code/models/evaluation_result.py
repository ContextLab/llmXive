"""
Data model for storing evaluation results of a model.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np
import json

@dataclass
class EvaluationResult:
    """
    Stores the results of a model evaluation run.
    
    Attributes:
        model_type (str): Identifier for the model type (e.g., 'GCN', 'LinearRegression').
        metrics (Dict[str, float]): Dictionary of metric names to values (MAE, RMSE, R2, etc.).
        predictions (Optional[np.ndarray]): Array of predicted values.
        targets (Optional[np.ndarray]): Array of true target values.
        errors (Optional[np.ndarray]): Array of prediction errors (pred - target).
        hyperparameters (Dict[str, Any]): Dictionary of model hyperparameters.
        metadata (Dict[str, Any]): Additional metadata about the run.
    """
    model_type: str
    metrics: Dict[str, float] = field(default_factory=dict)
    predictions: Optional[np.ndarray] = None
    targets: Optional[np.ndarray] = None
    errors: Optional[np.ndarray] = None
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure numpy arrays are properly typed."""
        if self.predictions is not None and not isinstance(self.predictions, np.ndarray):
            self.predictions = np.array(self.predictions)
        if self.targets is not None and not isinstance(self.targets, np.ndarray):
            self.targets = np.array(self.targets)
        if self.errors is not None and not isinstance(self.errors, np.ndarray):
            self.errors = np.array(self.errors)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the evaluation result to a dictionary."""
        return {
            'model_type': self.model_type,
            'metrics': self.metrics,
            'predictions': self.predictions.tolist() if self.predictions is not None else None,
            'targets': self.targets.tolist() if self.targets is not None else None,
            'errors': self.errors.tolist() if self.errors is not None else None,
            'hyperparameters': self.hyperparameters,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationResult':
        """Create an EvaluationResult instance from a dictionary."""
        predictions = None
        if data.get('predictions') is not None:
            predictions = np.array(data['predictions'])
        
        targets = None
        if data.get('targets') is not None:
            targets = np.array(data['targets'])
        
        errors = None
        if data.get('errors') is not None:
            errors = np.array(data['errors'])

        return cls(
            model_type=data['model_type'],
            metrics=data.get('metrics', {}),
            predictions=predictions,
            targets=targets,
            errors=errors,
            hyperparameters=data.get('hyperparameters', {}),
            metadata=data.get('metadata', {})
        )

    def to_json(self) -> str:
        """Serialize the evaluation result to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> 'EvaluationResult':
        """Deserialize an evaluation result from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    def add_metric(self, name: str, value: float) -> None:
        """Add or update a metric."""
        self.metrics[name] = value

    def get_metric(self, name: str, default: Optional[float] = None) -> Optional[float]:
        """Retrieve a metric value."""
        return self.metrics.get(name, default)