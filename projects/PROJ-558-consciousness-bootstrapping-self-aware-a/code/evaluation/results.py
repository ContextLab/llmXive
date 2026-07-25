from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path


@dataclass
class EvaluationResult:
    """
    Dataclass representing the results of a model evaluation run.

    Attributes:
        run_id: Unique identifier for this evaluation run.
        checkpoint_id: Identifier of the model checkpoint evaluated.
        model_type: Type of model evaluated (e.g., 'recursive', 'baseline').
        dataset_name: Name of the dataset used for evaluation (e.g., 'gsm8k', 'mmlu').
        seed: Random seed used for the evaluation.
        timestamp: Timestamp of the evaluation run.
        metrics: Dictionary of metric names to their calculated values.
        raw_predictions: List of raw prediction dictionaries (optional).
        config_snapshot: Snapshot of the configuration used during evaluation.
    """
    run_id: str
    checkpoint_id: str
    model_type: str
    dataset_name: str
    seed: int
    timestamp: datetime = field(default_factory=datetime.now)
    metrics: Dict[str, float] = field(default_factory=dict)
    raw_predictions: List[Dict[str, Any]] = field(default_factory=list)
    config_snapshot: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the evaluation result to a dictionary for JSON serialization."""
        return {
            "run_id": self.run_id,
            "checkpoint_id": self.checkpoint_id,
            "model_type": self.model_type,
            "dataset_name": self.dataset_name,
            "seed": self.seed,
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics,
            "raw_predictions": self.raw_predictions,
            "config_snapshot": self.config_snapshot
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize the evaluation result to a JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvaluationResult":
        """Create an EvaluationResult instance from a dictionary."""
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> "EvaluationResult":
        """Create an EvaluationResult instance from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    def save_to_file(self, output_path: Path) -> None:
        """Save this evaluation result to a JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def load_from_file(cls, input_path: Path) -> "EvaluationResult":
        """Load an EvaluationResult instance from a JSON file."""
        with open(input_path, "r", encoding="utf-8") as f:
            return cls.from_json(f.read())