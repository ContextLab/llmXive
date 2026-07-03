"""
Experiment logging and artifact storage utility.
Writes JSON/CSV logs to artifacts/results/ directory.
"""
import json
import csv
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import threading

# Ensure the artifacts/results directory exists
ARTIFACTS_DIR = Path(__file__).resolve().parent.parent.parent / "artifacts" / "results"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Thread-safe lock for file writing
_file_lock = threading.Lock()


class RunLogger:
    """
    Context-managed logger for a specific experiment run.
    Collects metrics and metadata, writing them to JSON and CSV files on exit.
    """
    def __init__(self, run_id: str, output_dir: Optional[Path] = None):
        self.run_id = run_id
        self.output_dir = output_dir or ARTIFACTS_DIR
        self.metrics: Dict[str, Any] = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "metrics": {}
        }
        self.history: List[Dict[str, Any]] = []
        self._initialized = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.flush()
        return False

    def log_metric(self, name: str, value: Any, step: Optional[int] = None):
        """Log a single metric value."""
        entry = {"name": name, "value": value, "step": step, "timestamp": datetime.now().isoformat()}
        self.history.append(entry)
        self.metrics["metrics"][name] = value
        logger.info(f"[{self.run_id}] Logged metric: {name} = {value}")

    def log_metadata(self, key: str, value: Any):
        """Log static metadata (e.g., hyperparameters)."""
        self.metrics[key] = value
        logger.info(f"[{self.run_id}] Logged metadata: {key} = {value}")

    def flush(self):
        """Write all collected data to JSON and CSV files."""
        if not self.history:
            logger.warning(f"[{self.run_id}] No metrics to flush.")
            return

        with _file_lock:
            # Write JSON summary
            json_path = self.output_dir / f"run_{self.run_id}_summary.json"
            try:
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(self.metrics, f, indent=2, default=str)
                logger.info(f"[{self.run_id}] Wrote JSON summary to {json_path}")
            except IOError as e:
                logger.error(f"[{self.run_id}] Failed to write JSON: {e}")

            # Write CSV history
            csv_path = self.output_dir / f"run_{self.run_id}_metrics.csv"
            try:
                with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=["timestamp", "step", "name", "value"])
                    writer.writeheader()
                    for row in self.history:
                        writer.writerow(row)
                logger.info(f"[{self.run_id}] Wrote CSV history to {csv_path}")
            except IOError as e:
                logger.error(f"[{self.run_id}] Failed to write CSV: {e}")


def setup_experiment_logger(run_id: str) -> RunLogger:
    """
    Factory function to create a configured RunLogger instance.
    """
    return RunLogger(run_id)


def log_to_json(data: Dict[str, Any], filename: str, append: bool = False) -> Path:
    """
    Utility to write a dictionary directly to a JSON file in artifacts/results/.
    """
    filepath = ARTIFACTS_DIR / filename
    with _file_lock:
        if append and filepath.exists():
            existing = json.loads(filepath.read_text())
            if isinstance(existing, list):
                existing.append(data)
            else:
                # If existing is a dict and we are appending, we might need to merge or wrap
                existing = [existing, data]
        else:
            existing = data if not isinstance(data, list) else data

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(existing, f, indent=2, default=str)
    
    logger.info(f"Wrote JSON to {filepath}")
    return filepath


def log_to_csv(rows: List[Dict[str, Any]], filename: str, fieldnames: Optional[List[str]] = None):
    """
    Utility to write a list of dictionaries to a CSV file in artifacts/results/.
    """
    filepath = ARTIFACTS_DIR / filename
    if not fieldnames and rows:
        fieldnames = list(rows[0].keys())
    elif not fieldnames:
        fieldnames = []

    with _file_lock:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    
    logger.info(f"Wrote CSV to {filepath}")


def main():
    """
    Demo entry point to verify logger functionality.
    Creates a test run, logs some metrics, and flushes.
    """
    print("Running logger demo...")
    test_run_id = "demo_test_001"
    
    with setup_experiment_logger(test_run_id) as lg:
        lg.log_metadata("model", "gpt2-medium")
        lg.log_metadata("dataset", "babi_task3")
        lg.log_metric("loss", 0.543, step=1)
        lg.log_metric("loss", 0.412, step=2)
        lg.log_metric("accuracy", 0.85, step=2)
        lg.log_metric("memory_mb", 4096, step=2)
    
    print(f"Demo complete. Check {ARTIFACTS_DIR} for output files.")


if __name__ == "__main__":
    main()