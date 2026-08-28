"""
Mixin class for adding logging capabilities to simulation components.
"""

import logging
from typing import Optional, Dict, Any

from src.logging_config import MetricLogger, get_metric_logger


class LoggingMixin:
    """
    Mixin to add logging functionality to simulation classes.

    Provides methods to log step metrics including coherence_score,
    diversity_score, and step_latency.
    """

    def __init__(self, run_id: str, *args, **kwargs):
        """
        Initialize logging for this component.

        Args:
            run_id: Unique identifier for this simulation run
            *args: Passed to parent class
            **kwargs: Passed to parent class
        """
        super().__init__(*args, **kwargs)
        self.metric_logger: Optional[MetricLogger] = None
        self.run_id = run_id

        # Initialize logger if not already done
        if not hasattr(self, '_logger_initialized'):
            self._logger_initialized = True
            self.metric_logger = get_metric_logger(run_id)

    def log_step(
        self,
        coherence_score: float,
        diversity_score: float,
        step_latency: float,
        step_id: Optional[int] = None,
        extra_metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log metrics for the current simulation step.

        Args:
            coherence_score: Coherence metric value
            diversity_score: Diversity metric value
            step_latency: Time taken for this step in seconds
            step_id: Optional step identifier
            extra_metrics: Optional dict of additional metrics
        """
        if self.metric_logger is None:
            self.metric_logger = get_metric_logger(self.run_id)

        self.metric_logger.log_step_metrics(
            coherence_score=coherence_score,
            diversity_score=diversity_score,
            step_latency=step_latency,
            step_id=step_id,
            additional_metrics=extra_metrics
        )

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
            avg_coherence: Average coherence score
            avg_diversity: Average diversity score
            avg_latency: Average step latency
            status: Run status
        """
        if self.metric_logger is None:
            self.metric_logger = get_metric_logger(self.run_id)

        self.metric_logger.log_run_summary(
            total_steps=total_steps,
            avg_coherence=avg_coherence,
            avg_diversity=avg_diversity,
            avg_latency=avg_latency,
            status=status
        )
