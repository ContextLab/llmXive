from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import numpy as np
import json


@dataclass
class EvaluationResult:
    """
    Data model storing the results of a model evaluation.
    Contains aggregate metrics and per-sample predictions/errors.
    """
    model_type: str
    mae: float
    rmse: float
    r2: float
    predictions: np.ndarray
    targets: np.ndarray
    smiles_list: List[str]
    errors: np.ndarray
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the EvaluationResult to a dictionary."""
        return {
            "model_type": self.model_type,
            "mae": self.mae,
            "rmse": self.rmse,
            "r2": self.r2,
            "predictions": self.predictions.tolist(),
            "targets": self.targets.tolist(),
            "smiles_list": self.smiles_list,
            "errors": self.errors.tolist(),
            "hyperparameters": self.hyperparameters,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvaluationResult":
        """Create an EvaluationResult instance from a dictionary."""
        return cls(
            model_type=data["model_type"],
            mae=data["mae"],
            rmse=data["rmse"],
            r2=data["r2"],
            predictions=np.array(data["predictions"]),
            targets=np.array(data["targets"]),
            smiles_list=data["smiles_list"],
            errors=np.array(data["errors"]),
            hyperparameters=data.get("hyperparameters", {}),
            metadata=data.get("metadata", {})
        )

    def to_json(self) -> str:
        """Serialize the EvaluationResult to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "EvaluationResult":
        """Deserialize an EvaluationResult from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    def summary(self) -> str:
        """Return a human-readable summary of the evaluation results."""
        return (
            f"Evaluation Result for {self.model_type}:\n"
            f"  MAE: {self.mae:.4f} Å²\n"
            f"  RMSE: {self.rmse:.4f} Å²\n"
            f"  R²: {self.r2:.4f}\n"
            f"  Samples: {len(self.smiles_list)}"
        )
