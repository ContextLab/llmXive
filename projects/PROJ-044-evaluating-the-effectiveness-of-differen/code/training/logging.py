"""
Experiment logging infrastructure for Federated Learning with Differential Privacy.

This module provides utilities to log training metrics to both CSV and JSON formats.
It supports appending to existing logs, creating new log files, and managing
structured experiment data.
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dataclasses import dataclass, asdict


@dataclass
class TrainingMetrics:
    """Data container for a single training round's metrics."""
    seed: int
    alpha: float
    epsilon: float
    dataset: str
    round: int
    global_accuracy: float
    global_loss: float
    minority_accuracy: Optional[float] = None
    majority_accuracy: Optional[float] = None
    privacy_budget_used: float = 0.0
    is_time_limited: bool = False
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_row(self) -> List[str]:
        """Convert to a list of strings for CSV row."""
        return [
            str(self.seed),
            str(self.alpha),
            str(self.epsilon),
            self.dataset,
            str(self.round),
            f"{self.global_accuracy:.6f}",
            f"{self.global_loss:.6f}",
            f"{self.minority_accuracy:.6f}" if self.minority_accuracy is not None else "NA",
            f"{self.majority_accuracy:.6f}" if self.majority_accuracy is not None else "NA",
            f"{self.privacy_budget_used:.6f}",
            str(self.is_time_limited),
            self.timestamp
        ]


class ExperimentLogger:
    """
    Manages logging of training metrics to both CSV and JSON files.

    Supports:
    - Creating new log files if they don't exist
    - Appending to existing log files
    - Flushing data to disk periodically
    - Retrieving all logged metrics
    """

    def __init__(self, base_dir: Union[str, Path], experiment_id: str):
        """
        Initialize the logger.

        Args:
            base_dir: Directory where log files will be stored (e.g., 'results/logs')
            experiment_id: Unique identifier for this experiment run
        """
        self.base_dir = Path(base_dir)
        self.experiment_id = experiment_id
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.csv_path = self.base_dir / f"{experiment_id}_metrics.csv"
        self.json_path = self.base_dir / f"{experiment_id}_metrics.json"

        self._buffer: List[TrainingMetrics] = []
        self._csv_header_written = False

        # Initialize files if they don't exist
        self._initialize_files()

    def _initialize_files(self):
        """Create log files if they don't exist and write CSV headers."""
        if not self.csv_path.exists():
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                header = [
                    'seed', 'alpha', 'epsilon', 'dataset', 'round',
                    'global_accuracy', 'global_loss', 'minority_accuracy',
                    'majority_accuracy', 'privacy_budget_used', 'is_time_limited',
                    'timestamp'
                ]
                writer.writerow(header)
            self._csv_header_written = True
        else:
            self._csv_header_written = True

        if not self.json_path.exists():
            with open(self.json_path, 'w') as f:
                json.dump([], f)

    def log(self, metrics: TrainingMetrics):
        """
        Log a single set of metrics.

        Args:
            metrics: TrainingMetrics object containing the data to log
        """
        self._buffer.append(metrics)

    def flush(self):
        """Flush all buffered metrics to disk."""
        if not self._buffer:
            return

        # Append to CSV
        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            for metrics in self._buffer:
                writer.writerow(metrics.to_row())

        # Append to JSON
        with open(self.json_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

        for metrics in self._buffer:
            data.append(metrics.to_dict())

        with open(self.json_path, 'w') as f:
            json.dump(data, f, indent=2)

        self._buffer.clear()

    def get_all_metrics(self) -> List[Dict[str, Any]]:
        """Retrieve all logged metrics from the JSON file."""
        if not self.json_path.exists():
            return []

        with open(self.json_path, 'r') as f:
            return json.load(f)

    def close(self):
        """Flush any remaining data and close the logger."""
        self.flush()


def log_training_round(
    logger: ExperimentLogger,
    seed: int,
    alpha: float,
    epsilon: float,
    dataset: str,
    round_num: int,
    global_accuracy: float,
    global_loss: float,
    privacy_budget_used: float = 0.0,
    minority_accuracy: Optional[float] = None,
    majority_accuracy: Optional[float] = None,
    is_time_limited: bool = False
):
    """
    Convenience function to log a training round.

    Args:
        logger: ExperimentLogger instance
        seed: Random seed used for the experiment
        alpha: Dirichlet concentration parameter
        epsilon: Privacy budget (epsilon)
        dataset: Name of the dataset (e.g., 'femnist', 'shakespeare')
        round_num: Current training round number
        global_accuracy: Global model accuracy
        global_loss: Global model loss
        privacy_budget_used: Amount of privacy budget consumed
        minority_accuracy: Accuracy on minority class clients (optional)
        majority_accuracy: Accuracy on majority class clients (optional)
        is_time_limited: Flag indicating if the run was time-limited
    """
    metrics = TrainingMetrics(
        seed=seed,
        alpha=alpha,
        epsilon=epsilon,
        dataset=dataset,
        round=round_num,
        global_accuracy=global_accuracy,
        global_loss=global_loss,
        minority_accuracy=minority_accuracy,
        majority_accuracy=majority_accuracy,
        privacy_budget_used=privacy_budget_used,
        is_time_limited=is_time_limited
    )
    logger.log(metrics)
    logger.flush()


def load_metrics_csv(filepath: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Load metrics from a CSV file.

    Args:
        filepath: Path to the CSV file

    Returns:
        List of dictionaries containing the metrics
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return []

    results = []
    with open(filepath, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            row['seed'] = int(row['seed'])
            row['alpha'] = float(row['alpha'])
            row['epsilon'] = float(row['epsilon'])
            row['round'] = int(row['round'])
            row['global_accuracy'] = float(row['global_accuracy'])
            row['global_loss'] = float(row['global_loss'])
            row['privacy_budget_used'] = float(row['privacy_budget_used'])
            row['is_time_limited'] = row['is_time_limited'] == 'True'

            # Handle optional fields
            if row['minority_accuracy'] != 'NA':
                row['minority_accuracy'] = float(row['minority_accuracy'])
            else:
                row['minority_accuracy'] = None

            if row['majority_accuracy'] != 'NA':
                row['majority_accuracy'] = float(row['majority_accuracy'])
            else:
                row['majority_accuracy'] = None

            results.append(row)

    return results


def load_metrics_json(filepath: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Load metrics from a JSON file.

    Args:
        filepath: Path to the JSON file

    Returns:
        List of dictionaries containing the metrics
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return []

    with open(filepath, 'r') as f:
        return json.load(f)