"""
Experiment logging and artifact storage utilities.

Configures structured logging to write JSON and CSV files to artifacts/results/.
"""
import json
import csv
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import logging

# Ensure output directory exists
ARTIFACTS_DIR = Path("artifacts")
RESULTS_DIR = ARTIFACTS_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Configure standard logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class ExperimentLogger:
    """
    Manages logging of experiment metrics, hyperparameters, and run metadata.
    Writes outputs to JSON and CSV formats in artifacts/results/.
    """

    def __init__(self, run_name: str, run_id: Optional[str] = None):
        """
        Initialize the logger for a specific experiment run.

        Args:
            run_name: Human-readable name for the experiment.
            run_id: Unique identifier for the run (defaults to timestamp).
        """
        self.run_name = run_name
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.base_path = RESULTS_DIR
        self.metrics: List[Dict[str, Any]] = []
        self.hyperparams: Dict[str, Any] = {}
        self.start_time: Optional[float] = None
        
        # Ensure run-specific directory
        self.run_dir = self.base_path / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def start_run(self, hyperparameters: Dict[str, Any]) -> None:
        """
        Record the start of an experiment run.

        Args:
            hyperparameters: Dictionary of configuration parameters.
        """
        self.start_time = time.time()
        self.hyperparams = hyperparameters
        
        # Log initial hyperparameters to JSON
        self._save_json("hyperparams_start.json", {
            "run_name": self.run_name,
            "run_id": self.run_id,
            "timestamp": datetime.now().isoformat(),
            "hyperparameters": hyperparameters
        })
        
        logger.info(f"Started run: {self.run_name} (ID: {self.run_id})")

    def log_metric(self, metric_name: str, value: Union[int, float, str], 
                   step: Optional[int] = None, **extra: Any) -> None:
        """
        Log a single metric value.

        Args:
            metric_name: Name of the metric.
            value: Value of the metric.
            step: Optional step/epoch number.
            **extra: Additional context data to store with the metric.
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "metric_name": metric_name,
            "value": value,
            "step": step,
            **extra
        }
        self.metrics.append(entry)
        
        # Append to CSV immediately for robustness
        self._append_csv("metrics.csv", entry)
        
        logger.debug(f"Logged metric: {metric_name} = {value}")

    def log_epoch_metrics(self, epoch: int, metrics: Dict[str, Union[int, float]]) -> None:
        """
        Log a batch of metrics for a specific epoch.

        Args:
            epoch: Epoch number.
            metrics: Dictionary of metric names to values.
        """
        for name, value in metrics.items():
            self.log_metric(name, value, step=epoch)

    def end_run(self, status: str = "completed") -> Dict[str, Any]:
        """
        Finalize the run, saving summary data and runtime.

        Args:
            status: Final status of the run (e.g., 'completed', 'failed').

        Returns:
            Dictionary containing the run summary.
        """
        if self.start_time is None:
            raise RuntimeError("Run not started. Call start_run() first.")

        end_time = time.time()
        runtime = end_time - self.start_time

        summary = {
            "run_name": self.run_name,
            "run_id": self.run_id,
            "status": status,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "end_time": datetime.now().isoformat(),
            "runtime_seconds": runtime,
            "hyperparameters": self.hyperparams,
            "total_metrics_logged": len(self.metrics)
        }

        # Save final summary JSON
        self._save_json("run_summary.json", summary)
        
        # Save all metrics to a consolidated JSON as well
        self._save_json("metrics_full.json", {
            "run_id": self.run_id,
            "metrics": self.metrics
        })

        logger.info(f"Ended run: {self.run_name} (Runtime: {runtime:.2f}s, Status: {status})")
        
        return summary

    def _save_json(self, filename: str, data: Dict[str, Any]) -> None:
        """Helper to save data as JSON."""
        filepath = self.run_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

    def _append_csv(self, filename: str, row: Dict[str, Any]) -> None:
        """Helper to append a row to a CSV file."""
        filepath = self.run_dir / filename
        file_exists = filepath.exists()
        
        with open(filepath, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)


def get_logger_for_run(run_name: str, run_id: Optional[str] = None) -> ExperimentLogger:
    """
    Factory function to create a new experiment logger.

    Args:
        run_name: Name of the experiment.
        run_id: Optional unique ID.

    Returns:
        Configured ExperimentLogger instance.
    """
    return ExperimentLogger(run_name, run_id)


def load_run_summary(run_id: str) -> Optional[Dict[str, Any]]:
    """
    Load the summary JSON for a completed run.

    Args:
        run_id: The ID of the run to load.

    Returns:
        Dictionary of run summary data, or None if not found.
    """
    filepath = RESULTS_DIR / run_id / "run_summary.json"
    if not filepath.exists():
        return None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)