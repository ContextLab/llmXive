"""
EvaluationResult entity for serialization of benchmark evaluation outcomes.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path


@dataclass
class EvaluationResult:
    """
    Represents the result of running a model on a benchmark dataset.
    """
    result_id: str
    model_checkpoint_id: str
    model_type: str  # 'recursive', 'baseline', 'shuffled'
    dataset: str  # 'gsm8k', 'mmlu'
    metrics: Dict[str, float]
    raw_predictions: Optional[List[Dict[str, Any]]] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    config_snapshot: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "result_id": self.result_id,
            "model_checkpoint_id": self.model_checkpoint_id,
            "model_type": self.model_type,
            "dataset": self.dataset,
            "metrics": self.metrics,
            "raw_predictions": self.raw_predictions,
            "created_at": self.created_at,
            "config_snapshot": self.config_snapshot
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationResult':
        """Deserialize from dictionary."""
        return cls(
            result_id=data["result_id"],
            model_checkpoint_id=data["model_checkpoint_id"],
            model_type=data["model_type"],
            dataset=data["dataset"],
            metrics=data["metrics"],
            raw_predictions=data.get("raw_predictions"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            config_snapshot=data.get("config_snapshot")
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'EvaluationResult':
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def save(self, output_path: str) -> str:
        """
        Save the evaluation result to a JSON file.
        Returns the path to the saved file.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
        return str(path)

    @classmethod
    def load(cls, input_path: str) -> 'EvaluationResult':
        """Load an evaluation result from a JSON file."""
        with open(input_path, 'r', encoding='utf-8') as f:
            return cls.from_json(f.read())