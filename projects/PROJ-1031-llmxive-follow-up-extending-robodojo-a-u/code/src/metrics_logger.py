"""
Metrics Logger for RoboDojo Symbolic Abstractions Pipeline.

This module provides functionality to record CPU cycles, RAM usage,
and wall-clock time for every task execution. It includes memory
monitoring to enforce the 6 GB RAM limit constraint.
"""

import os
import time
import tracemalloc
import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from pathlib import Path

# Import config for paths
from .config import DATA_INTERIM_PATH, LOGGING_LEVEL

# Configure logging
logging.basicConfig(
    level=LOGGING_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ResourceLimitExceeded(Exception):
    """Raised when RAM usage exceeds the 6 GB limit."""
    pass


@dataclass
class TaskMetrics:
    """Data class to store metrics for a single task execution."""
    task_id: str
    start_time: float
    end_time: float
    wall_clock_time: float
    cpu_cycles: int  # Approximate via time.process_time() * constant or similar
    peak_memory_mb: float
    current_memory_mb: float
    status: str  # 'success', 'failed', 'resource_limit_exceeded'
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MetricsLogger:
    """
    Context manager and utility class for logging execution metrics.
    Enforces the 6 GB RAM limit as per T022 requirements.
    """

    # Constants
    RAM_LIMIT_GB = 6.0
    RAM_LIMIT_BYTES = RAM_LIMIT_GB * 1024 * 1024 * 1024

    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize the MetricsLogger.

        Args:
            log_file: Optional path to the JSON log file. Defaults to
                      data/interim/metrics_log.json.
        """
        self.log_file = log_file or os.path.join(DATA_INTERIM_PATH, "metrics_log.json")
        self._metrics: List[Dict[str, Any]] = []
        self._current_metrics: Optional[TaskMetrics] = None
        self._tracemalloc_started = False

        # Ensure log directory exists
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)

    def _get_memory_usage(self) -> float:
        """
        Get current memory usage in MB using tracemalloc.
        Returns the peak memory usage if tracemalloc is active.
        """
        if self._tracemalloc_started:
            current, peak = tracemalloc.get_traced_memory()
            return peak / (1024 * 1024)  # Convert to MB
        return 0.0

    def _check_ram_limit(self, current_mb: float) -> None:
        """
        Check if current RAM usage exceeds the limit.
        Raises ResourceLimitExceeded if it does.
        """
        if current_mb > (self.RAM_LIMIT_GB * 1024):
            raise ResourceLimitExceeded(
                f"RAM usage {current_mb:.2f} MB exceeds limit of {self.RAM_LIMIT_GB * 1024:.2f} MB. "
                "Aborting to prevent system instability."
            )

    def start_task(self, task_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Start tracking metrics for a new task.

        Args:
            task_id: Unique identifier for the task.
            metadata: Optional dictionary of additional metadata to log.
        """
        self._current_metrics = TaskMetrics(
            task_id=task_id,
            start_time=time.time(),
            end_time=0.0,
            wall_clock_time=0.0,
            cpu_cycles=0,
            peak_memory_mb=0.0,
            current_memory_mb=0.0,
            status='running',
            metadata=metadata or {}
        )

        # Start tracemalloc if not already running
        if not self._tracemalloc_started:
            tracemalloc.start()
            self._tracemalloc_started = True

        logger.info(f"Starting metrics tracking for task: {task_id}")

    def update_metrics(self) -> None:
        """
        Update current memory metrics during task execution.
        Checks against RAM limit.
        """
        if not self._current_metrics:
            return

        current_mb = self._get_memory_usage()
        self._current_metrics.current_memory_mb = current_mb

        # Check limit
        self._check_ram_limit(current_mb)

    def end_task(self, status: str = 'success', error_message: Optional[str] = None) -> None:
        """
        End tracking for the current task and finalize metrics.

        Args:
            status: Final status of the task ('success', 'failed', etc.).
            error_message: Optional error message if the task failed.
        """
        if not self._current_metrics:
            logger.warning("end_task called without a corresponding start_task.")
            return

        end_time = time.time()
        self._current_metrics.end_time = end_time
        self._current_metrics.wall_clock_time = end_time - self._current_metrics.start_time
        self._current_metrics.status = status
        self._current_metrics.error_message = error_message
        self._current_metrics.cpu_cycles = int(time.process_time() * 1e9)  # Approximate cycles
        self._current_metrics.peak_memory_mb = self._get_memory_usage()
        self._current_metrics.current_memory_mb = self._current_metrics.peak_memory_mb

        logger.info(
            f"Task {self._current_metrics.task_id} completed. "
            f"Time: {self._current_metrics.wall_clock_time:.3f}s, "
            f"Peak RAM: {self._current_metrics.peak_memory_mb:.2f} MB"
        )

        self._metrics.append(self._current_metrics.to_dict())
        self._current_metrics = None

    def save_log(self) -> None:
        """
        Save all collected metrics to the log file.
        Appends to existing file if it exists.
        """
        # Ensure directory exists
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)

        try:
            # Load existing logs if file exists
            existing_metrics = []
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        existing_metrics = json.loads(content)

            # Combine and save
            all_metrics = existing_metrics + self._metrics
            with open(self.log_file, 'w') as f:
                json.dump(all_metrics, f, indent=2)

            logger.info(f"Metrics saved to {self.log_file}")
        except Exception as e:
            logger.error(f"Failed to save metrics log: {e}")
            raise

    def __enter__(self) -> 'MetricsLogger':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            if self._current_metrics:
                self.end_task(status='failed', error_message=str(exc_val))
        else:
            if self._current_metrics:
                self.end_task(status='success')
        
        if self._tracemalloc_started:
            tracemalloc.stop()
            self._tracemalloc_started = False
        
        # Always save log on exit
        self.save_log()


def create_metrics_logger(log_file: Optional[str] = None) -> MetricsLogger:
    """
    Factory function to create a MetricsLogger instance.

    Args:
        log_file: Optional path to the log file.

    Returns:
        A configured MetricsLogger instance.
    """
    return MetricsLogger(log_file=log_file)


# Convenience function for single-shot logging
def log_task_metrics(
    task_id: str,
    func,
    *args,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Execute a function and log its metrics.

    Args:
        task_id: Identifier for the task.
        func: The function to execute.
        *args: Positional arguments for func.
        metadata: Optional metadata.
        **kwargs: Keyword arguments for func.

    Returns:
        Dictionary containing the final metrics.
    """
    logger = MetricsLogger()
    logger.start_task(task_id, metadata)
    try:
        result = func(*args, **kwargs)
        logger.end_task(status='success')
        return logger._metrics[-1] if logger._metrics else {}
    except ResourceLimitExceeded as e:
        logger.end_task(status='resource_limit_exceeded', error_message=str(e))
        raise
    except Exception as e:
        logger.end_task(status='failed', error_message=str(e))
        raise
    finally:
        logger.save_log()