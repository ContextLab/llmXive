"""
Data model for evaluation results.

This module defines the EvaluationResult dataclass used to store
and serialize the results of model evaluations, including metrics
and raw prediction data.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import json
import numpy as np


@dataclass
class EvaluationResult:
    """
    Container for model evaluation metrics and prediction data.

    Attributes:
        model_type (str): Identifier for the model architecture (e.g., 'GCN', 'Baseline').
        mae (float): Mean Absolute Error.
        rmse (float): Root Mean Squared Error.
        r2 (float): Coefficient of determination (R-squared).
        predictions (list): List of predicted values.
        errors (list): List of errors (y_true - y_pred).
    """
    model_type: str
    mae: float
    rmse: float
    r2: float
    predictions: List[float] = field(default_factory=list)
    errors: List[float] = field(default_factory=list)

    def to_json(self) -> str:
        """
        Serialize the evaluation result to a JSON string.

        Returns:
            str: JSON representation of the object.
        """
        data = {
            "model_type": self.model_type,
            "mae": self.mae,
            "rmse": self.rmse,
            "r2": self.r2,
            "predictions": self.predictions,
            "errors": self.errors
        }
        return json.dumps(data, indent=2)

    def summary(self) -> Dict[str, Any]:
        """
        Generate a human-readable summary of the evaluation results.

        Returns:
            dict: A dictionary containing formatted metrics.
        """
        return {
            "Model Type": self.model_type,
            "MAE (Å²)": f"{self.mae:.4f}",
            "RMSE (Å²)": f"{self.rmse:.4f}",
            "R² Score": f"{self.r2:.4f}",
            "Number of Predictions": len(self.predictions),
            "Max Error": f"{max(abs(e) for e in self.errors):.4f}" if self.errors else "N/A",
            "Mean Error": f"{sum(self.errors) / len(self.errors):.4f}" if self.errors else "N/A"
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationResult':
        """
        Create an EvaluationResult instance from a dictionary.

        Args:
            data (dict): Dictionary containing evaluation data.

        Returns:
            EvaluationResult: Instantiated object.
        """
        return cls(
            model_type=data["model_type"],
            mae=float(data["mae"]),
            rmse=float(data["rmse"]),
            r2=float(data["r2"]),
            predictions=[float(x) for x in data.get("predictions", [])],
            errors=[float(x) for x in data.get("errors", [])]
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the instance to a dictionary.

        Returns:
            dict: Dictionary representation of the object.
        """
        return {
            "model_type": self.model_type,
            "mae": self.mae,
            "rmse": self.rmse,
            "r2": self.r2,
            "predictions": self.predictions,
            "errors": self.errors
        }