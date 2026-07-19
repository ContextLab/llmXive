"""
EvaluationResult data model.

Stores the results of model evaluation, including metrics, predictions,
and ground truth values.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np
import json


@dataclass
class EvaluationResult:
    """
    Data class representing evaluation results.

    Attributes:
        model_name (str): Name of the model being evaluated.
        dataset_split (str): Name of the dataset split (e.g., 'train', 'test').
        predictions (np.ndarray): Array of predicted values.
        targets (np.ndarray): Array of ground truth target values.
        mae (float): Mean Absolute Error.
        rmse (float): Root Mean Squared Error.
        r2 (float): R-squared coefficient of determination.
        num_samples (int): Number of samples evaluated.
        metadata (Dict[str, Any]): Additional evaluation metadata (e.g., hyperparameters).
    """
    model_name: str
    dataset_split: str
    predictions: np.ndarray
    targets: np.ndarray
    mae: float
    rmse: float
    r2: float
    num_samples: int
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate inputs after initialization."""
        if self.predictions.shape != self.targets.shape:
            raise ValueError(
                f"Predictions shape {self.predictions.shape} must match targets shape {self.targets.shape}"
            )
        if self.num_samples != len(self.predictions):
            self.num_samples = len(self.predictions)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to a JSON-serializable dictionary."""
        return {
            "model_name": self.model_name,
            "dataset_split": self.dataset_split,
            "predictions": self.predictions.tolist(),
            "targets": self.targets.tolist(),
            "mae": self.mae,
            "rmse": self.rmse,
            "r2": self.r2,
            "num_samples": self.num_samples,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvaluationResult":
        """Create an EvaluationResult instance from a dictionary."""
        return cls(
            model_name=data["model_name"],
            dataset_split=data["dataset_split"],
            predictions=np.array(data["predictions"]),
            targets=np.array(data["targets"]),
            mae=data["mae"],
            rmse=data["rmse"],
            r2=data["r2"],
            num_samples=data["num_samples"],
            metadata=data.get("metadata", {})
        )

    def to_json(self) -> str:
        """Serialize result to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "EvaluationResult":
        """Deserialize result from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    def save(self, path: str) -> None:
        """Save the evaluation result to a JSON file."""
        with open(path, 'w') as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, path: str) -> "EvaluationResult":
        """Load an evaluation result from a JSON file."""
        with open(path, 'r') as f:
            return cls.from_dict(json.load(f))
