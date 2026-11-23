"""
Active monitoring context manager for tracking resource usage (memory, time).
Required for FR-010 and available for all phases.
"""
import os
import time
import logging
import json
import psutil
from typing import Optional, Dict, Any
from contextlib import contextmanager

# Configure logger for this module specifically to avoid circular imports
# with the project's main logging.py if it exists.
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)
if not _logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    _logger.addHandler(handler)


class ActiveMonitor:
    """
    Context manager to track peak memory usage (RSS) and wall-clock time.
    """
    def __init__(self, task_name: str = "unnamed_task"):
        self.task_name = task_name
        self.process = psutil.Process(os.getpid())
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.peak_memory_mb: float = 0.0
        self.initial_memory_mb: float = 0.0
        self._sample_interval: float = 0.1  # 100ms sampling
        self._samples: list = []

    def __enter__(self):
        self.start_time = time.time()
        self.initial_memory_mb = self.process.memory_info().rss / (1024 * 1024)
        self.peak_memory_mb = self.initial_memory_mb
        _logger.info(f"ActiveMonitor started for task: {self.task_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        final_memory_mb = self.process.memory_info().rss / (1024 * 1024)
        self.peak_memory_mb = max(self.peak_memory_mb, final_memory_mb)
        
        duration_seconds = self.end_time - self.start_time
        
        _logger.info(
            f"ActiveMonitor finished for task: {self.task_name}. "
            f"Duration: {duration_seconds:.2f}s, Peak Memory: {self.peak_memory_mb:.2f}MB"
        )
        
        # Log to a resource file if the directory exists, otherwise just log to console
        resource_log_path = "data/reports/resource_log.json"
        try:
            if os.path.exists("data/reports"):
                self._append_resource_log(resource_log_path)
        except Exception as e:
            _logger.warning(f"Could not write resource log to {resource_log_path}: {e}")

        return False  # Do not suppress exceptions

    def _append_resource_log(self, path: str):
        """Appends current run stats to a JSONL file or creates it."""
        log_entry = {
            "task_name": self.task_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.end_time - self.start_time,
            "peak_memory_mb": self.peak_memory_mb,
            "initial_memory_mb": self.initial_memory_mb
        }
        
        with open(path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def get_stats(self) -> Dict[str, Any]:
        """Returns a dictionary of the collected statistics."""
        if not self.end_time:
            raise RuntimeError("Monitor has not finished execution yet.")
        
        return {
            "task_name": self.task_name,
            "duration_seconds": self.end_time - self.start_time,
            "peak_memory_mb": self.peak_memory_mb,
            "initial_memory_mb": self.initial_memory_mb
        }


@contextmanager
def monitor_execution(task_name: str = "unnamed_task"):
    """
    Decorator/Context manager wrapper for simpler usage.
    Usage:
      with monitor_execution("my_task"):
          # code to monitor
          pass
    """
    monitor = ActiveMonitor(task_name)
    with monitor:
        yield monitor