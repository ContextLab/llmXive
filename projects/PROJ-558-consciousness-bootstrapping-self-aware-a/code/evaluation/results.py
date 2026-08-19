"""
EvaluationResult entity for serializing benchmark outcomes and metrics.

This module defines the `EvaluationResult` dataclass, which encapsulates
the results of model evaluation against benchmarks (e.g., GSM8K, MMLU).
It supports strict serialization to JSON for reproducibility and analysis.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path

@dataclass
class EvaluationResult:
    """
    Represents the aggregated results of a model evaluation run.

    Attributes:
        result_id: Unique identifier for this evaluation run.
        model_name: Name of the model evaluated.
        checkpoint_id: Reference to the ModelCheckpoint used.
        dataset_name: Name of the dataset used for evaluation (e.g., 'gsm8k', 'mmlu').
        timestamp: ISO 8601 formatted string of when the evaluation was completed.
        metrics: Dictionary of computed metrics (e.g., accuracy, self_consistency, brier_score).
        raw_predictions: Optional list of raw prediction details (question, answer, path, confidence).
        config_snapshot: Snapshot of the evaluation configuration (temperature, top_p, etc.).
        total_samples: Total number of samples evaluated.
        valid_samples: Number of samples with valid predictions.
    """
    result_id: str
    model_name: str
    checkpoint_id: str
    dataset_name: str
    timestamp: str
    metrics: Dict[str, float] = field(default_factory=dict)
    raw_predictions: List[Dict[str, Any]] = field(default_factory=list)
    config_snapshot: Dict[str, Any] = field(default_factory=dict)
    total_samples: int = 0
    valid_samples: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the evaluation result to a dictionary for JSON serialization.
        """
        return {
            "result_id": self.result_id,
            "model_name": self.model_name,
            "checkpoint_id": self.checkpoint_id,
            "dataset_name": self.dataset_name,
            "timestamp": self.timestamp,
            "metrics": self.metrics,
            "raw_predictions": self.raw_predictions,
            "config_snapshot": self.config_snapshot,
            "total_samples": self.total_samples,
            "valid_samples": self.valid_samples
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationResult':
        """
        Reconstructs an EvaluationResult from a dictionary.
        """
        return cls(
            result_id=data["result_id"],
            model_name=data["model_name"],
            checkpoint_id=data["checkpoint_id"],
            dataset_name=data["dataset_name"],
            timestamp=data["timestamp"],
            metrics=data.get("metrics", {}),
            raw_predictions=data.get("raw_predictions", []),
            config_snapshot=data.get("config_snapshot", {}),
            total_samples=data.get("total_samples", 0),
            valid_samples=data.get("valid_samples", 0)
        )

    def save(self, output_path: Path) -> None:
        """
        Saves the evaluation result to a JSON file.

        Args:
            output_path: The file path where the result JSON will be written.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    @classmethod
    def load(cls, input_path: Path) -> 'EvaluationResult':
        """
        Loads an evaluation result from a JSON file.

        Args:
            input_path: The file path to read the result from.

        Returns:
            An EvaluationResult instance populated with the file data.
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Evaluation result not found at {input_path}")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls.from_dict(data)

    def add_metric(self, key: str, value: float) -> None:
        """
        Adds or updates a metric in the metrics dictionary.

        Args:
            key: The name of the metric.
            value: The value of the metric.
        """
        self.metrics[key] = value

    def add_prediction(self, prediction: Dict[str, Any]) -> None:
        """
        Adds a raw prediction to the list.

        Args:
            prediction: A dictionary containing prediction details.
        """
        self.raw_predictions.append(prediction)
        self.total_samples += 1
        if prediction.get("is_valid", False):
            self.valid_samples += 1