"""
EvaluationResult entity for serialization of benchmark outputs.

This module defines the `EvaluationResult` dataclass, which encapsulates
the results of model evaluation against benchmarks (GSM8K, MMLU, etc.).
It supports serialization to JSON for downstream statistical analysis.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path


@dataclass
class EvaluationResult:
    """
    Represents the result of a model evaluation run.

    Attributes:
        model_id: Identifier of the model being evaluated.
        benchmark_name: Name of the benchmark (e.g., 'gsm8k', 'mmlu').
        timestamp: ISO format timestamp of the evaluation run.
        metrics: Dictionary of computed metrics (e.g., accuracy, self_consistency).
        predictions: List of prediction dictionaries (question, answer, confidence).
        metadata: Additional run metadata (e.g., temperature, seed).
    """
    model_id: str
    benchmark_name: str
    timestamp: str
    metrics: Dict[str, float]
    predictions: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary for JSON serialization."""
        return {
            "model_id": self.model_id,
            "benchmark_name": self.benchmark_name,
            "timestamp": self.timestamp,
            "metrics": self.metrics,
            "predictions": self.predictions,
            "metadata": self.metadata
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the result to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvaluationResult":
        """Deserialize a result from a dictionary."""
        return cls(
            model_id=data["model_id"],
            benchmark_name=data["benchmark_name"],
            timestamp=data["timestamp"],
            metrics=data["metrics"],
            predictions=data["predictions"],
            metadata=data.get("metadata", {})
        )

    @classmethod
    def from_json(cls, json_str: str) -> "EvaluationResult":
        """Deserialize a result from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    def save(self, output_path: Path) -> Path:
        """
        Save the evaluation result to a JSON file.
        Creates parent directories if they do not exist.
        Returns the path to the saved file.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
        return output_path