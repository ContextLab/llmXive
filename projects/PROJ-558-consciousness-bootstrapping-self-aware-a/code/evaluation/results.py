"""
EvaluationResult dataclass for storing benchmark evaluation outcomes.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path

@dataclass
class EvaluationResult:
    """
    Represents the results of a model evaluation on a benchmark.

    Attributes:
        result_id: Unique identifier for this evaluation run.
        model_checkpoint_id: ID of the checkpoint that was evaluated.
        benchmark_name: Name of the benchmark (e.g., 'gsm8k', 'mmlu').
        timestamp: Time when the evaluation was completed.
        metrics: Dictionary of calculated metrics (e.g., accuracy, self_consistency).
        raw_predictions: List of raw prediction strings or objects.
        raw_ground_truth: List of corresponding ground truth values.
        metadata: Additional metadata about the evaluation run.
    """
    result_id: str
    model_checkpoint_id: str
    benchmark_name: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metrics: Dict[str, float] = field(default_factory=dict)
    raw_predictions: List[Any] = field(default_factory=list)
    raw_ground_truth: List[Any] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the evaluation result to a dictionary for serialization."""
        return {
            'result_id': self.result_id,
            'model_checkpoint_id': self.model_checkpoint_id,
            'benchmark_name': self.benchmark_name,
            'timestamp': self.timestamp,
            'metrics': self.metrics,
            'raw_predictions': self.raw_predictions,
            'raw_ground_truth': self.raw_ground_truth,
            'metadata': self.metadata
        }

    def to_json(self, path: Optional[Path] = None) -> str:
        """
        Serialize the evaluation result to a JSON string.
        Optionally save to a file if path is provided.
        """
        data = self.to_dict()
        json_str = json.dumps(data, indent=2, default=str)
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(json_str)
        return json_str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationResult':
        """Create an EvaluationResult instance from a dictionary."""
        return cls(
            result_id=data['result_id'],
            model_checkpoint_id=data['model_checkpoint_id'],
            benchmark_name=data['benchmark_name'],
            timestamp=data.get('timestamp', datetime.now().isoformat()),
            metrics=data.get('metrics', {}),
            raw_predictions=data.get('raw_predictions', []),
            raw_ground_truth=data.get('raw_ground_truth', []),
            metadata=data.get('metadata', {})
        )

    @classmethod
    def from_json(cls, path: Path) -> 'EvaluationResult':
        """Load an EvaluationResult from a JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)