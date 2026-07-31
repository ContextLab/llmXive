"""
Data model for evaluation results.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np
import json


@dataclass
class EvaluationResult:
    """
    Stores the results of model evaluation on a dataset.

    Attributes:
        model_name: Name of the model evaluated.
        dataset_name: Name of the dataset used.
        metrics: Dictionary of metric names to values (e.g., {'mae': 0.5}).
        predictions: Array of predicted values.
        targets: Array of actual target values.
        metadata: Additional context about the evaluation run.
    """
    model_name: str
    dataset_name: str
    metrics: Dict[str, float] = field(default_factory=dict)
    predictions: Optional[np.ndarray] = None
    targets: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_metric(self, name: str, value: float) -> None:
        """Add a single metric to the results."""
        self.metrics[name] = value

    def get_metric(self, name: str, default: Optional[float] = None) -> Optional[float]:
        """Retrieve a metric value by name."""
        return self.metrics.get(name, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary."""
        return {
            "model_name": self.model_name,
            "dataset_name": self.dataset_name,
            "metrics": self.metrics,
            "predictions": self.predictions.tolist() if self.predictions is not None else None,
            "targets": self.targets.tolist() if self.targets is not None else None,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Serialize the evaluation result to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvaluationResult":
        """Reconstruct an EvaluationResult from a dictionary."""
        return cls(
            model_name=data["model_name"],
            dataset_name=data["dataset_name"],
            metrics=data.get("metrics", {}),
            predictions=np.array(data["predictions"]) if data.get("predictions") is not None else None,
            targets=np.array(data["targets"]) if data.get("targets") is not None else None,
            metadata=data.get("metadata", {})
        )

    @classmethod
    def from_json(cls, json_str: str) -> "EvaluationResult":
        """Reconstruct an EvaluationResult from a JSON string."""
        return cls.from_dict(json.loads(json_str))
