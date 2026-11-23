"""
Logging infrastructure for llmXive simulation pipeline.

This module configures logging to record simulation metrics including
coherence_score, diversity_score, and step_latency at specified intervals.
"""

import logging
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Ensure output directory exists
LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

def setup_logging(run_id: str, log_level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger for a specific simulation run.

    Args:
        run_id: Unique identifier for this simulation run
        log_level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(f"llmxive.{run_id}")
    logger.setLevel(log_level)

    # Prevent duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    metric_formatter = logging.Formatter('%(message)s')

    # File handler for general logs
    log_file = LOG_DIR / f"{run_id}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)

    # File handler for metrics (JSON format)
    metrics_file = LOG_DIR / f"{run_id}_metrics.jsonl"
    metrics_handler = logging.FileHandler(metrics_file)
    metrics_handler.setLevel(logging.INFO)
    metrics_handler.setFormatter(metric_formatter)
    logger.addHandler(metrics_handler)

    # Console handler for live output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(detailed_formatter)
    logger.addHandler(console_handler)

    return logger


class MetricLogger:
    """
    Logger specifically for simulation metrics.

    Records coherence_score, diversity_score, and step_latency
    at specified intervals in JSON Lines format.
    """

    def __init__(self, logger: logging.Logger, run_id: str):
        """
        Initialize the metric logger.

        Args:
            logger: The configured logger instance
            run_id: Unique identifier for this simulation run
        """
        self.logger = logger
        self.run_id = run_id
        self.metrics_file = LOG_DIR / f"{run_id}_metrics.jsonl"
        self.start_time = datetime.now()
        self.step_count = 0

    def log_step_metrics(
        self,
        coherence_score: float,
        diversity_score: float,
        step_latency: float,
        step_id: Optional[int] = None,
        additional_metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log metrics for a simulation step.

        Args:
            coherence_score: Coherence metric value
            diversity_score: Diversity metric value
            step_latency: Time taken for this step in seconds
            step_id: Optional step identifier (auto-incremented if None)
            additional_metrics: Optional dict of extra metrics to log
        """
        if step_id is None:
            self.step_count += 1
            step_id = self.step_count

        elapsed_time = (datetime.now() - self.start_time).total_seconds()

        metric_record = {
            "run_id": self.run_id,
            "step_id": step_id,
            "elapsed_time": elapsed_time,
            "coherence_score": coherence_score,
            "diversity_score": diversity_score,
            "step_latency": step_latency,
            "timestamp": datetime.now().isoformat()
        }

        if additional_metrics:
            metric_record.update(additional_metrics)

        # Log as JSON line
        self.logger.info(json.dumps(metric_record))

    def log_run_summary(
        self,
        total_steps: int,
        avg_coherence: float,
        avg_diversity: float,
        avg_latency: float,
        status: str = "completed"
    ) -> None:
        """
        Log a summary of the simulation run.

        Args:
            total_steps: Total number of steps executed
            avg_coherence: Average coherence score across all steps
            avg_diversity: Average diversity score across all steps
            avg_latency: Average step latency across all steps
            status: Run status (completed, failed, interrupted)
        """
        summary = {
            "run_id": self.run_id,
            "total_steps": total_steps,
            "avg_coherence": avg_coherence,
            "avg_diversity": avg_diversity,
            "avg_latency": avg_latency,
            "status": status,
            "end_time": datetime.now().isoformat()
        }

        self.logger.info(json.dumps({"summary": summary}))


def get_metric_logger(run_id: str, log_level: int = logging.INFO) -> MetricLogger:
    """
    Convenience function to get a configured MetricLogger.

    Args:
        run_id: Unique identifier for this simulation run
        log_level: Logging level (default: INFO)

    Returns:
        Configured MetricLogger instance
    """
    logger = setup_logging(run_id, log_level)
    return MetricLogger(logger, run_id)
