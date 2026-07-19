"""
EvaluationResult data model.
Stores evaluation metrics and predictions for model performance assessment.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np
import json

@dataclass
class EvaluationResult:
    """
    Data model for evaluation results.
    
    Attributes:
        model_name: Name/identifier of the model being evaluated.
        predictions: Array of predicted values.
        targets: Array of true values.
        mae: Mean Absolute Error.
        rmse: Root Mean Squared Error.
        r2: R-squared coefficient.
        samples: Number of samples evaluated.
        metadata: Additional metadata dictionary.
    """
    model_name: str
    predictions: np.ndarray
    targets: np.ndarray
    mae: Optional[float] = None
    rmse: Optional[float] = None
    r2: Optional[float] = None
    samples: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate and compute metrics if not provided."""
        if self.samples == 0:
            self.samples = len(self.predictions)
        
        # Validate lengths match
        if len(self.predictions) != len(self.targets):
            raise ValueError(
                f"Predictions length ({len(self.predictions)}) "
                f"must match targets length ({len(self.targets)})"
            )

    def compute_metrics(self) -> Dict[str, float]:
        """Compute evaluation metrics if not already set."""
        if self.mae is None or self.rmse is None or self.r2 is None:
            from eval.metrics import calculate_mae, calculate_rmse, calculate_r2
            self.mae = calculate_mae(self.predictions, self.targets)
            self.rmse = calculate_rmse(self.predictions, self.targets)
            self.r2 = calculate_r2(self.predictions, self.targets)
        
        return {
            "mae": self.mae,
            "rmse": self.rmse,
            "r2": self.r2,
            "samples": self.samples
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert evaluation result to dictionary."""
        metrics = self.compute_metrics()
        return {
            "model_name": self.model_name,
            "predictions": self.predictions.tolist(),
            "targets": self.targets.tolist(),
            "mae": metrics["mae"],
            "rmse": metrics["rmse"],
            "r2": metrics["r2"],
            "samples": metrics["samples"],
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Convert evaluation result to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvaluationResult":
        """Create EvaluationResult from dictionary."""
        return cls(
            model_name=data["model_name"],
            predictions=np.array(data["predictions"]),
            targets=np.array(data["targets"]),
            mae=data.get("mae"),
            rmse=data.get("rmse"),
            r2=data.get("r2"),
            samples=data.get("samples", len(data["predictions"])),
            metadata=data.get("metadata", {})
        )

    @classmethod
    def from_json(cls, json_str: str) -> "EvaluationResult":
        """Create EvaluationResult from JSON string."""
        return cls.from_dict(json.loads(json_str))
