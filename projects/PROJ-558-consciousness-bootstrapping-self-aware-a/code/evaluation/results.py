from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path

@dataclass
class EvaluationResult:
    """
    Represents the results of a model evaluation on a benchmark.
    Contains metrics, raw data summaries, and metadata for analysis.
    """
    evaluation_id: str
    model_checkpoint_id: str
    benchmark_name: str  # e.g., 'gsm8k_self_consistency', 'mmlu_standard'
    dataset_name: str
    num_samples: int
    metrics: Dict[str, float] = field(default_factory=dict)
    raw_data_summary: Dict[str, Any] = field(default_factory=dict)
    generated_paths_count: int = 0
    majority_vote_accuracy: Optional[float] = None
    self_consistency_score: Optional[float] = None
    calibration_metrics: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    config_snapshot: Dict[str, Any] = field(default_factory=dict)
    error_log: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert evaluation result to dictionary for JSON serialization."""
        return {
            'evaluation_id': self.evaluation_id,
            'model_checkpoint_id': self.model_checkpoint_id,
            'benchmark_name': self.benchmark_name,
            'dataset_name': self.dataset_name,
            'num_samples': self.num_samples,
            'metrics': self.metrics,
            'raw_data_summary': self.raw_data_summary,
            'generated_paths_count': self.generated_paths_count,
            'majority_vote_accuracy': self.majority_vote_accuracy,
            'self_consistency_score': self.self_consistency_score,
            'calibration_metrics': self.calibration_metrics,
            'created_at': self.created_at.isoformat(),
            'config_snapshot': self.config_snapshot,
            'error_log': self.error_log
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize evaluation result to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    def save_to_file(self, output_path: str) -> Path:
        """
        Save evaluation result to a JSON file.
        Returns the path to the saved file.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
        return path

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationResult':
        """Create an EvaluationResult instance from a dictionary."""
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

    @classmethod
    def load_from_file(cls, file_path: str) -> 'EvaluationResult':
        """Load evaluation result from a JSON file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Evaluation result file not found: {file_path}")
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
