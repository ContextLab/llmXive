import json
import csv
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import logging

class Logger:
    """
    Custom logger for handling JSON/CSV output for training artifacts.
    """
    def __init__(self, output_dir: str, log_level: str = "INFO"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup standard logging
        self.logger = logging.getLogger("llmxive")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        if not self.logger.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def log_training_run(self, run_id: str, config: Dict[str, Any], status: str = "STARTED"):
        """Log the start/end of a training run."""
        timestamp = datetime.now().isoformat()
        record = {
            "type": "training_run",
            "run_id": run_id,
            "timestamp": timestamp,
            "status": status,
            "config": config
        }
        self.logger.info(f"Training Run {run_id}: {status}")
        # Write to JSONL
        log_path = self.output_dir / "training_runs.jsonl"
        with open(log_path, 'a') as f:
            f.write(json.dumps(record) + '\n')

    def log_gating_signal(self, run_id: str, step: int, signal_data: Dict[str, Any]):
        """Log a gating signal event."""
        timestamp = datetime.now().isoformat()
        record = {
            "type": "gating_signal",
            "run_id": run_id,
            "step": step,
            "timestamp": timestamp,
            **signal_data
        }
        log_path = self.output_dir / "gating_signals.jsonl"
        with open(log_path, 'a') as f:
            f.write(json.dumps(record) + '\n')

    def log_metric(self, run_id: str, step: int, metric_name: str, value: float):
        """Log a specific metric value."""
        timestamp = datetime.now().isoformat()
        record = {
            "type": "metric",
            "run_id": run_id,
            "step": step,
            "timestamp": timestamp,
            "metric_name": metric_name,
            "value": value
        }
        log_path = self.output_dir / "metrics.jsonl"
        with open(log_path, 'a') as f:
            f.write(json.dumps(record) + '\n')

def get_logger(output_dir: str = "data/processed", log_level: str = "INFO") -> Logger:
    """Factory function to get a logger instance."""
    return Logger(output_dir, log_level)

def log_training_run(run_id: str, config: Dict[str, Any], status: str = "STARTED"):
    """Convenience function for quick logging."""
    logger = get_logger()
    logger.log_training_run(run_id, config, status)

def log_gating_signal(run_id: str, step: int, signal_data: Dict[str, Any]):
    """Convenience function for gating signal logging."""
    logger = get_logger()
    logger.log_gating_signal(run_id, step, signal_data)

def close_logger():
    """Cleanup logging handlers if necessary."""
    pass # Standard logging cleanup is usually automatic
