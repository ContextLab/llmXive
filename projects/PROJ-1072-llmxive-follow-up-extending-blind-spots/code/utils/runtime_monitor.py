import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from .logging_config import get_logger

logger = get_logger(__name__)

# Global 6-hour limit in seconds
GLOBAL_RUNTIME_LIMIT_SECONDS = 6 * 60 * 60
PER_TASK_TIMEOUT_SECONDS = 10 * 60  # 10 minutes per task

class RuntimeMonitor:
    """
    Monitors cumulative runtime to enforce the global 6-hour limit (FR-009).
    Tracks elapsed time and checks if starting a new task would exceed the limit.
    """
    def __init__(self, output_dir: Optional[Path] = None):
        self.start_time: Optional[float] = None
        self.elapsed_time: float = 0.0
        self.tasks_processed: int = 0
        self.output_dir = output_dir or Path("data/results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(__name__)

    def start(self):
        """Start the runtime timer."""
        if self.start_time is None:
            self.start_time = time.time()
            self.logger.info("RuntimeMonitor started.")

    def stop(self):
        """Stop the timer and update elapsed time."""
        if self.start_time is not None:
            self.elapsed_time += time.time() - self.start_time
            self.start_time = None
            self.logger.info(f"RuntimeMonitor stopped. Total elapsed: {self.elapsed_time:.2f}s")

    def check_before_task(self) -> bool:
        """
        Check if starting a new task would exceed the global limit.
        Returns True if it is SAFE to start a new task.
        Returns False if the global limit would be exceeded.
        """
        if self.start_time is None:
            current_elapsed = self.elapsed_time
        else:
            current_elapsed = self.elapsed_time + (time.time() - self.start_time)

        projected_time = current_elapsed + PER_TASK_TIMEOUT_SECONDS

        if projected_time > GLOBAL_RUNTIME_LIMIT_SECONDS:
            self.logger.error(
                f"ERR_TIMEOUT_GLOBAL: Starting a new task would exceed the 6-hour limit. "
                f"Current elapsed: {current_elapsed:.2f}s, Projected: {projected_time:.2f}s"
            )
            return False
        return True

    def record_task_completion(self):
        """Record that a task was successfully processed."""
        self.tasks_processed += 1

    def halt_and_report(self):
        """
        Halt execution and generate the runtime_limit_reached.json artifact.
        This is called when the global limit is reached.
        """
        if self.start_time is not None:
            self.stop()

        report = {
            "elapsed_time": self.elapsed_time,
            "reason": "Runtime limit exceeded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "effective_sample_size": self.tasks_processed
        }

        report_path = self.output_dir / "runtime_limit_reached.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        self.logger.critical(
            f"Global runtime limit reached. Report saved to {report_path}. "
            f"Processed {self.tasks_processed} tasks."
        )
        return report

    def get_elapsed_time(self) -> float:
        """Get current elapsed time in seconds."""
        if self.start_time is None:
            return self.elapsed_time
        return self.elapsed_time + (time.time() - self.start_time)

def create_monitor(output_dir: Optional[Path] = None) -> RuntimeMonitor:
    """Create and return a RuntimeMonitor instance."""
    return RuntimeMonitor(output_dir)
