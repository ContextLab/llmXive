import os
import time
import tracemalloc
import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
import psutil
import resource

from src.config import BASE_DIR, RAM_LIMIT_GB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TaskMetrics:
    """
    Data class to store metrics for a single task execution.
    """
    task_id: str
    cpu_cycles: int
    ram_mb: float
    wall_clock_s: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class MetricsLogger:
    """
    Logger to record CPU cycles, RAM usage, and wall-clock time for every task.
    Supports streaming to a JSONL file to avoid loading all data into memory.
    """
    output_path: str
    _current_process: Optional[psutil.Process] = field(default=None, init=False)
    _start_time: Optional[float] = field(default=None, init=False)
    _start_ram: Optional[float] = field(default=None, init=False)
    _start_cpu: Optional[int] = field(default=None, init=False)

    def __post_init__(self):
        # Ensure output directory exists
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        self._current_process = psutil.Process()
        logger.info(f"MetricsLogger initialized. Output path: {self.output_path}")

    def _get_ram_mb(self) -> float:
        """Get current RAM usage in MB."""
        if self._current_process is None:
            return 0.0
        # RSS (Resident Set Size) in bytes
        rss = self._current_process.memory_info().rss
        return rss / (1024 * 1024)

    def _get_cpu_cycles(self) -> int:
        """
        Estimate CPU cycles used.
        Note: Python doesn't expose raw CPU cycles directly.
        We use process CPU times (user + system) as a proxy for CPU work.
        Multiplying by an estimated clock speed (e.g., 2.0 GHz) gives an approximate cycle count.
        This is an estimate suitable for relative comparisons.
        """
        if self._current_process is None:
            return 0
        # Get CPU times in seconds
        times = self._current_process.cpu_times()
        total_cpu_seconds = times.user + times.system
        # Estimate: assume 2.0 GHz average clock speed for calculation
        # This is a heuristic for relative comparison across tasks
        estimated_clock_speed_hz = 2.0e9
        return int(total_cpu_seconds * estimated_clock_speed_hz)

    def start_task(self, task_id: str) -> None:
        """Start measuring metrics for a specific task."""
        if self._start_time is not None:
            logger.warning("A task is already being measured. Stopping previous measurement.")
            self.stop_task()

        self._start_time = time.time()
        # Force a garbage collection to get a cleaner baseline for memory
        import gc
        gc.collect()
        
        # Snapshot memory before task
        self._start_ram = self._get_ram_mb()
        
        # Snapshot CPU times before task
        if self._current_process:
            self._start_cpu = self._get_cpu_cycles()
        
        logger.info(f"Started measuring metrics for task: {task_id}")

    def stop_task(self, task_id: str) -> TaskMetrics:
        """Stop measuring and return the TaskMetrics object."""
        if self._start_time is None:
            raise RuntimeError("No task is currently being measured. Call start_task first.")

        end_time = time.time()
        end_ram = self._get_ram_mb()
        end_cpu = self._get_cpu_cycles()

        wall_clock_s = end_time - self._start_time
        ram_mb = end_ram - self._start_ram if self._start_ram else end_ram
        cpu_cycles = end_cpu - self._start_cpu if self._start_cpu else end_cpu

        # Ensure non-negative values (in case of counter wrap or measurement noise)
        if ram_mb < 0: ram_mb = 0.0
        if cpu_cycles < 0: cpu_cycles = 0

        metrics = TaskMetrics(
            task_id=task_id,
            cpu_cycles=cpu_cycles,
            ram_mb=ram_mb,
            wall_clock_s=wall_clock_s,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )

        self._start_time = None
        self._start_ram = None
        self._start_cpu = None

        logger.info(f"Task {task_id} completed. Metrics: {metrics}")
        return metrics

    def log_metrics(self, metrics: TaskMetrics) -> None:
        """
        Append metrics to the output file in JSONL format.
        This ensures memory efficiency for large numbers of tasks.
        """
        with open(self.output_path, 'a') as f:
            f.write(json.dumps(metrics.to_dict()) + '\n')
        logger.debug(f"Logged metrics for task {metrics.task_id} to {self.output_path}")

    def check_ram_limit(self, task_id: str) -> None:
        """
        Check if current RAM usage exceeds the limit defined in config.
        Raises ResourceLimitExceeded if the limit is breached.
        """
        current_ram = self._get_ram_mb()
        if current_ram > RAM_LIMIT_GB * 1024:
            error_msg = (
                f"RAM limit exceeded for task {task_id}. "
                f"Current usage: {current_ram:.2f} MB, Limit: {RAM_LIMIT_GB * 1024:.2f} MB"
            )
            logger.error(error_msg)
            raise ResourceLimitExceeded(error_msg)

class ResourceLimitExceeded(Exception):
    """Raised when a resource limit (e.g., RAM) is exceeded."""
    pass

def create_metrics_logger(output_path: Optional[str] = None) -> MetricsLogger:
    """
    Factory function to create a MetricsLogger instance.
    Default output path is code/data/interim/metrics.jsonl.
    """
    if output_path is None:
        output_path = os.path.join(BASE_DIR, "data", "interim", "metrics.jsonl")
    return MetricsLogger(output_path)

def log_task_metrics(task_id: str, logger_instance: Optional[MetricsLogger] = None) -> TaskMetrics:
    """
    Convenience function to start and stop metrics logging for a task context.
    If logger_instance is not provided, a new one is created with default path.
    
    Usage:
    with log_task_metrics("task_123") as metrics:
        # do work
        return metrics
    """
    # This is a helper that mimics a context manager behavior if needed, 
    # but the primary interface is via the MetricsLogger class methods.
    # For direct usage:
    if logger_instance is None:
        logger_instance = create_metrics_logger()
    
    logger_instance.start_task(task_id)
    # The caller is expected to do work and then call stop_task manually
    # to ensure the work is actually done before stopping.
    # However, to make this a true utility, we can't easily wrap arbitrary code
    # without a context manager. Let's stick to the class methods for clarity
    # or provide a context manager wrapper.
    return logger_instance # Return the logger so user can call stop_task
    
# Context Manager wrapper for convenience
class MetricsContext:
    def __init__(self, task_id: str, logger_instance: MetricsLogger):
        self.task_id = task_id
        self.logger = logger_instance
        self.metrics: Optional[TaskMetrics] = None

    def __enter__(self):
        self.logger.start_task(self.task_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.metrics = self.logger.stop_task(self.task_id)
        self.logger.log_metrics(self.metrics)
        # Check RAM limit after task completion
        if self.metrics:
            # We check against the final state, or we could check periodically.
            # For strict compliance with T022, we check the peak or final.
            # Here we check the final RAM delta or total if we tracked peak.
            # The logger tracks current process RSS.
            # Let's assume the check should be done on the final measurement.
            try:
                self.logger.check_ram_limit(self.task_id)
            except ResourceLimitExceeded:
                # Re-raise to halt execution as per T022
                raise
        return False

def create_metrics_context(task_id: str, logger_instance: Optional[MetricsLogger] = None) -> MetricsContext:
    """
    Create a context manager for measuring metrics of a specific task.
    Usage:
    with create_metrics_context("task_123") as ctx:
        # do work
        final_metrics = ctx.metrics
    """
    if logger_instance is None:
        logger_instance = create_metrics_logger()
    return MetricsContext(task_id, logger_instance)