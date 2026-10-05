"""
Runtime Monitor Utility for Global Time-Bounded Execution.

Provides a context manager and helper functions to enforce a global
runtime limit (e.g., 6 hours) for the inference pipeline.

Enforces FR-009: Fixed wall-clock timeout per task and global runtime limit.
"""
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import signal
import sys

from .logging_config import get_logger

# Constants
GLOBAL_LIMIT_SECONDS = 21600  # 6 hours
TASK_TIMEOUT_SECONDS = 600    # 10 minutes
ERROR_CODE_TIMEOUT_GLOBAL = "ERR_TIMEOUT_GLOBAL"
ERROR_CODE_TIMEOUT_TASK = "ERR_TIMEOUT"

logger = get_logger(__name__)


class RuntimeMonitor:
    """
    Context manager to enforce global runtime limits for the inference loop.
    
    Checks elapsed time before starting each task. If the remaining time
    is insufficient to complete the next task (or if the global limit is
    reached), it halts execution immediately.
    """
    def __init__(self, output_path: str, global_limit: float = GLOBAL_LIMIT_SECONDS):
        self.global_limit = global_limit
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.output_path = Path(output_path)
        self.tasks_completed = 0
        self.tasks_skipped = 0
        self.reason: Optional[str] = None
        self._original_handler = None

    def __enter__(self):
        self.start_time = time.time()
        logger.info(f"Global runtime monitor started. Limit: {self.global_limit}s")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        elapsed = self.end_time - self.start_time
        
        if exc_type is not None:
            self.reason = f"Exception: {exc_type.__name__}: {exc_val}"
            self._write_status(elapsed, self.reason)
            # Allow exception to propagate if not a controlled halt
            if not isinstance(exc_val, SystemExit):
                return False
            return True
        
        # Normal exit
        if self.reason is None:
            self.reason = "Completed successfully"
        self._write_status(elapsed, self.reason)
        return False

    def check_time_before_task(self, task_index: int) -> bool:
        """
        Check if there is enough time to start the next task.
        
        Args:
            task_index: The index of the task about to be started (0-based).
        
        Returns:
            True if the task can proceed, False if the global limit is reached.
        
        Raises:
            SystemExit: If the global limit is exceeded, halts immediately with status report.
        """
        if self.start_time is None:
            raise RuntimeError("RuntimeMonitor not entered (use 'with' statement)")

        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # Check if we have at least TASK_TIMEOUT_SECONDS remaining
        # Logic: elapsed + TASK_TIMEOUT_SECONDS > global_limit => Halt
        if elapsed + TASK_TIMEOUT_SECONDS > self.global_limit:
            self.reason = "Runtime limit exceeded"
            self.tasks_completed = task_index  # Current index is the count of completed tasks
            self._write_status(elapsed, self.reason)
            logger.error(f"{ERROR_CODE_TIMEOUT_GLOBAL}: Global limit reached at {elapsed:.2f}s. Halting.")
            sys.exit(1)
        
        return True

    def record_task_complete(self):
        """Record that a task has been successfully completed."""
        self.tasks_completed += 1
        # Log progress periodically
        if self.tasks_completed % 10 == 0:
            elapsed = time.time() - self.start_time
            logger.info(f"Progress: {self.tasks_completed} tasks completed. Elapsed: {elapsed:.2f}s")

    def record_task_skipped(self):
        """Record that a task was skipped (e.g., timeout, error)."""
        self.tasks_skipped += 1

    def _write_status(self, elapsed_time: float, reason: str):
        """Write the runtime status JSON to the output file."""
        status = {
            "elapsed_time": round(elapsed_time, 2),
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "effective_sample_size": self.tasks_completed,
            "tasks_skipped": self.tasks_skipped,
            "global_limit_seconds": self.global_limit
        }
        
        # Ensure directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(status, f, indent=2)
        
        logger.info(f"Runtime status written to {self.output_path}")


def create_monitor(output_path: str, global_limit: float = GLOBAL_LIMIT_SECONDS) -> RuntimeMonitor:
    """
    Factory function to create a RuntimeMonitor instance.
    
    Args:
        output_path: Path to write the runtime status JSON (e.g., 'data/results/runtime_status.json').
        global_limit: Maximum allowed runtime in seconds.
    
    Returns:
        RuntimeMonitor instance.
    """
    return RuntimeMonitor(output_path, global_limit)
