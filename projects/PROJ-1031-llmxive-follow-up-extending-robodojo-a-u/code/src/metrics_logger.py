"""
Metrics logging module for tracking resource usage and performance.
"""
import os
import time
import tracemalloc
import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from src.config import BASE_DIR

logger = logging.getLogger(__name__)

@dataclass
class TaskMetrics:
    """Container for task execution metrics."""
    task_id: str
    planning_time_s: float
    peak_ram_mb: float
    status: str
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class ResourceLimitExceeded(Exception):
    """Exception raised when resource limits are exceeded."""
    pass

class MetricsLogger:
    """Logs metrics to files and console."""

    def __init__(self, output_dir: str = None):
        self.output_dir = output_dir or os.path.join(BASE_DIR, "data", "processed", "metrics")
        os.makedirs(self.output_dir, exist_ok=True)
        self.log_file = os.path.join(self.output_dir, "planning_metrics.jsonl")
        self.history: List[Dict[str, Any]] = []

    def log_task_metrics(self, metrics: Dict[str, Any], task_id: str = "unknown"):
        """Log a single task's metrics."""
        metrics["task_id"] = task_id
        metrics["timestamp"] = time.time()
        self.history.append(metrics)

        with open(self.log_file, "a") as f:
            f.write(json.dumps(metrics) + "\n")

        logger.info(f"Logged metrics for {task_id}: {metrics}")

    def get_history(self) -> List[Dict[str, Any]]:
        return self.history

def create_metrics_logger(output_dir: str = None) -> MetricsLogger:
    """Factory function to create a MetricsLogger instance."""
    return MetricsLogger(output_dir)

def log_task_metrics(task_id: str, metrics: Dict[str, Any], logger_instance: MetricsLogger = None):
    """Convenience function to log metrics."""
    if logger_instance is None:
        logger_instance = create_metrics_logger()
    logger_instance.log_task_metrics(metrics, task_id)

class MetricsContext:
    """Context manager for tracking metrics during a block of code."""

    def __init__(self, task_id: str, logger_instance: MetricsLogger):
        self.task_id = task_id
        self.logger = logger_instance
        self.start_time = None
        self.start_mem = None

    def __enter__(self):
        self.start_time = time.time()
        tracemalloc.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        metrics = {
            "planning_time_s": end_time - self.start_time,
            "peak_ram_mb": peak / (1024 ** 2),
            "status": "success" if exc_type is None else "failed"
        }

        self.logger.log_task_metrics(metrics, self.task_id)

        if exc_type is ResourceLimitExceeded:
            raise

        return False

def create_metrics_context(task_id: str, logger_instance: MetricsLogger) -> MetricsContext:
    """Factory function to create a MetricsContext."""
    return MetricsContext(task_id, logger_instance)