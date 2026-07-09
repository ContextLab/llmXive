from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path

@dataclass
class EvaluationResult:
    """
    Dataclass representing the results of a model evaluation run.
    Contains raw metrics, aggregated statistics, and metadata about the evaluation.
    """
    result_id: str
    model_checkpoint_id: str
    dataset_name: str
    timestamp: datetime
    config: dict
    metrics: Dict[str, float]
    raw_predictions: Optional[List[Dict[str, Any]]] = None
    per_sample_metrics: Optional[List[Dict[str, Any]]] = None
    error_analysis: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "result_id": self.result_id,
            "model_checkpoint_id": self.model_checkpoint_id,
            "dataset_name": self.dataset_name,
            "timestamp": self.timestamp.isoformat(),
            "config": self.config,
            "metrics": self.metrics,
            "raw_predictions": self.raw_predictions,
            "per_sample_metrics": self.per_sample_metrics,
            "error_analysis": self.error_analysis,
            "tags": self.tags,
            "metadata": self.metadata
        }

    def save_to_json(self, path: str) -> None:
        """Save evaluation result to a JSON file."""
        data = self.to_dict()
        # Ensure directory exists
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_json(cls, path: str) -> 'EvaluationResult':
        """Load evaluation result from a JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Convert timestamp string back to datetime
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

    def add_metric(self, name: str, value: float) -> None:
        """Add or update a metric."""
        self.metrics[name] = value

    def get_metric(self, name: str, default: Optional[float] = None) -> Optional[float]:
        """Get a metric value by name."""
        return self.metrics.get(name, default)
