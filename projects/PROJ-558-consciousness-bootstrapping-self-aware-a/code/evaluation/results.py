"""
EvaluationResult entity for serialization.

Defines the structure for storing results from benchmark evaluations,
including self-consistency metrics, calibration data, and raw predictions.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path

@dataclass
class EvaluationResult:
    """
    Represents the results of a model evaluation run on a specific benchmark.
    
    Attributes:
        result_id: Unique identifier for this evaluation run.
        model_name: Name of the model that was evaluated.
        checkpoint_id: ID of the checkpoint used for evaluation.
        benchmark_name: Name of the benchmark dataset (e.g., 'gsm8k', 'mmlu').
        timestamp: ISO format timestamp of when evaluation occurred.
        metrics: Dictionary of computed metrics (accuracy, brier_score, ece, etc.).
        raw_predictions: List of raw prediction dictionaries (question, answer, confidence).
        calibration_data: Optional dictionary containing binning data for calibration plots.
        metadata: Additional arbitrary metadata (e.g., seed, hyperparameters).
    """
    result_id: str
    model_name: str
    checkpoint_id: str
    benchmark_name: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metrics: Dict[str, Any] = field(default_factory=dict)
    raw_predictions: List[Dict[str, Any]] = field(default_factory=list)
    calibration_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary for serialization."""
        return {
            "result_id": self.result_id,
            "model_name": self.model_name,
            "checkpoint_id": self.checkpoint_id,
            "benchmark_name": self.benchmark_name,
            "timestamp": self.timestamp,
            "metrics": self.metrics,
            "raw_predictions": self.raw_predictions,
            "calibration_data": self.calibration_data,
            "metadata": self.metadata
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the result to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvaluationResult":
        """Load a result from a dictionary."""
        return cls(
            result_id=data["result_id"],
            model_name=data["model_name"],
            checkpoint_id=data["checkpoint_id"],
            benchmark_name=data["benchmark_name"],
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            metrics=data.get("metrics", {}),
            raw_predictions=data.get("raw_predictions", []),
            calibration_data=data.get("calibration_data"),
            metadata=data.get("metadata", {})
        )

    @classmethod
    def from_json(cls, json_str: str) -> "EvaluationResult":
        """Load a result from a JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def save(self, output_path: str) -> str:
        """
        Save the evaluation result to a JSON file.
        
        Args:
            output_path: Full path (including filename) to save the result.
            
        Returns:
            The path where the file was saved.
        """
        output_dir = str(Path(output_path).parent)
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
        
        return output_path

    def add_metric(self, key: str, value: float) -> None:
        """Add or update a single metric."""
        self.metrics[key] = value

    def add_prediction(self, prediction: Dict[str, Any]) -> None:
        """Add a single raw prediction to the list."""
        self.raw_predictions.append(prediction)