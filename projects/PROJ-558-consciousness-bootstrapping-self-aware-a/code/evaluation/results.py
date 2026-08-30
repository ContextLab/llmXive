"""
EvaluationResult entity for serialization.

This module defines the data structure used to store and serialize the results
of model evaluations, including metrics, predictions, and metadata. It adheres
to the project's serialization requirements and Constitution Principle III (Data Hygiene).
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
from pathlib import Path

@dataclass
class EvaluationResult:
    """
    Represents the results of a model evaluation run.

    Attributes:
        id: Unique identifier for this evaluation result.
        model_id: The ID of the model that was evaluated.
        dataset_name: The name of the dataset used for evaluation (e.g., 'gsm8k', 'mmlu').
        benchmark_name: The name of the benchmark protocol used (e.g., 'self_consistency_n10').
        metrics: A dictionary of computed metrics (e.g., accuracy, self_consistency, brier_score).
        raw_predictions: A list of raw prediction data (e.g., generated paths, confidence scores).
        aggregate_metrics: A dictionary of aggregated metrics across all samples.
        config_snapshot: A dictionary snapshot of the configuration used during evaluation.
        created_at: Timestamp of when the evaluation was completed.
        metadata: Additional arbitrary metadata.
    """
    id: str
    model_id: str
    dataset_name: str
    benchmark_name: str
    metrics: Dict[str, float] = field(default_factory=dict)
    raw_predictions: List[Dict[str, Any]] = field(default_factory=list)
    aggregate_metrics: Dict[str, float] = field(default_factory=dict)
    config_snapshot: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the evaluation result to a dictionary for JSON serialization.

        Returns:
            A dictionary representation of the evaluation result.
        """
        return {
            'id': self.id,
            'model_id': self.model_id,
            'dataset_name': self.dataset_name,
            'benchmark_name': self.benchmark_name,
            'metrics': self.metrics,
            'raw_predictions': self.raw_predictions,
            'aggregate_metrics': self.aggregate_metrics,
            'config_snapshot': self.config_snapshot,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }

    def to_json(self, indent: Optional[int] = 2) -> str:
        """
        Converts the evaluation result to a JSON string.

        Args:
            indent: Indentation level for pretty printing.

        Returns:
            A JSON string representation of the evaluation result.
        """
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationResult':
        """
        Creates an EvaluationResult instance from a dictionary.

        Args:
            data: A dictionary containing evaluation result data.

        Returns:
            An EvaluationResult instance.
        """
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()

        return cls(
            id=data['id'],
            model_id=data['model_id'],
            dataset_name=data['dataset_name'],
            benchmark_name=data['benchmark_name'],
            metrics=data.get('metrics', {}),
            raw_predictions=data.get('raw_predictions', []),
            aggregate_metrics=data.get('aggregate_metrics', {}),
            config_snapshot=data.get('config_snapshot', {}),
            created_at=created_at,
            metadata=data.get('metadata', {})
        )

    @classmethod
    def from_json(cls, json_str: str) -> 'EvaluationResult':
        """
        Creates an EvaluationResult instance from a JSON string.

        Args:
            json_str: A JSON string containing evaluation result data.

        Returns:
            An EvaluationResult instance.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def save_results(self, output_dir: str) -> str:
        """
        Saves the evaluation results to a JSON file.

        Args:
            output_dir: The directory where the results file will be saved.

        Returns:
            The path to the saved results file.
        """
        output_path = Path(output_dir) / f"{self.id}_results.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
        return str(output_path)

    @classmethod
    def load_results(cls, file_path: str) -> 'EvaluationResult':
        """
        Loads evaluation results from a JSON file.

        Args:
            file_path: The path to the results file.

        Returns:
            An EvaluationResult instance.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)