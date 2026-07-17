from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np
import json

@dataclass
class EvaluationResult:
    """
    Data model representing the results of a model evaluation.
    
    Attributes:
        model_name (str): Name of the model being evaluated.
        dataset_split (str): Name of the dataset split (e.g., 'train', 'test').
        mae (float): Mean Absolute Error.
        rmse (float): Root Mean Squared Error.
        r2 (float): R-squared coefficient.
        num_samples (int): Number of samples evaluated.
        predictions (Optional[np.ndarray]): Array of predicted values.
        targets (Optional[np.ndarray]): Array of true target values.
        metadata (Dict[str, Any]): Additional evaluation metadata.
    """
    model_name: str
    dataset_split: str
    mae: float
    rmse: float
    r2: float
    num_samples: int
    predictions: Optional[np.ndarray] = None
    targets: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure numpy arrays are correctly typed."""
        if self.predictions is not None and not isinstance(self.predictions, np.ndarray):
            self.predictions = np.array(self.predictions)
        if self.targets is not None and not isinstance(self.targets, np.ndarray):
            self.targets = np.array(self.targets)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the EvaluationResult instance to a dictionary."""
        return {
            "model_name": self.model_name,
            "dataset_split": self.dataset_split,
            "mae": self.mae,
            "rmse": self.rmse,
            "r2": self.r2,
            "num_samples": self.num_samples,
            "predictions": self.predictions.tolist() if self.predictions is not None else None,
            "targets": self.targets.tolist() if self.targets is not None else None,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Serialize the EvaluationResult instance to a JSON string."""
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvaluationResult":
        """Create an EvaluationResult instance from a dictionary."""
        predictions = data.get("predictions")
        targets = data.get("targets")
        if isinstance(predictions, list):
            predictions = np.array(predictions)
        if isinstance(targets, list):
            targets = np.array(targets)
        
        return cls(
            model_name=data["model_name"],
            dataset_split=data["dataset_split"],
            mae=data["mae"],
            rmse=data["rmse"],
            r2=data["r2"],
            num_samples=data["num_samples"],
            predictions=predictions,
            targets=targets,
            metadata=data.get("metadata", {})
        )

    def summary(self) -> str:
        """Return a human-readable summary of the evaluation."""
        return (
            f"Evaluation: {self.model_name} on {self.dataset_split}\n"
            f"  Samples: {self.num_samples}\n"
            f"  MAE: {self.mae:.4f} Å²\n"
            f"  RMSE: {self.rmse:.4f} Å²\n"
            f"  R²: {self.r2:.4f}"
        )
