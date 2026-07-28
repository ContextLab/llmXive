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
    Represents the results of a model evaluation.

    Attributes:
        model_name: Name of the evaluated model.
        mae: Mean Absolute Error.
        rmse: Root Mean Squared Error.
        r2: R-squared coefficient.
        predictions: List of predicted values.
        targets: List of target values.
        metrics: Additional metrics dictionary.
    """
    model_name: str
    mae: float
    rmse: float
    r2: float
    predictions: List[float] = field(default_factory=list)
    targets: List[float] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the evaluation result to a dictionary representation."""
        return {
            "model_name": self.model_name,
            "mae": self.mae,
            "rmse": self.rmse,
            "r2": self.r2,
            "predictions": self.predictions,
            "targets": self.targets,
            "metrics": self.metrics
        }

    def to_json(self) -> str:
        """Serialize the evaluation result to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvaluationResult":
        """Create an EvaluationResult instance from a dictionary."""
        return cls(
            model_name=data["model_name"],
            mae=data["mae"],
            rmse=data["rmse"],
            r2=data["r2"],
            predictions=data.get("predictions", []),
            targets=data.get("targets", []),
            metrics=data.get("metrics", {})
        )

    @classmethod
    def from_json(cls, json_str: str) -> "EvaluationResult":
        """Create an EvaluationResult instance from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
