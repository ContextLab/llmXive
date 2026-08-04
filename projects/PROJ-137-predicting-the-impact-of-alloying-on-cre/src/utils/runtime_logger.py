"""
Runtime Logger Utility for SC-005 Compliance.

This module provides functionality to measure, log, and report the total
execution time of the research pipeline. It ensures that the execution
duration is explicitly logged to both standard output and a dedicated
log file (`logs/runtime.log`) to serve as a measured outcome for
the Scientific Computing Constraint SC-005.

Usage:
    import time
    from src.utils.runtime_logger import RuntimeLogger

    logger = RuntimeLogger()
    logger.start()

    # ... pipeline execution ...

    logger.stop()
    logger.report()
"""

import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Ensure the project root is in the path if running as a script
# This handles cases where the script is run directly or imported
if __name__ == "__main__" and __package__ is None:
    ROOT_DIR = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(ROOT_DIR))

# Project paths relative to root
LOGS_DIR = Path("logs")
RUNTIME_LOG_FILE = LOGS_DIR / "runtime.log"

def _ensure_log_dir():
    """Ensure the logs directory exists."""
    if not LOGS_DIR.exists():
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

def _get_logger():
    """
    Configure and return a logger specifically for runtime metrics.
    This logger writes to both the console (stdout) and the file.
    """
    logger_name = "pipeline_runtime"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    _ensure_log_dir()

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File Handler (logs/runtime.log)
    file_handler = logging.FileHandler(RUNTIME_LOG_FILE)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Stream Handler (stdout)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger

class RuntimeLogger:
    """
    A context-manageable utility to track and log pipeline execution time.

    This class ensures that the total runtime is captured and reported
    in a format compliant with SC-005 requirements.
    """

    def __init__(self, logger_name: str = "pipeline_runtime"):
        self.logger = logging.getLogger(logger_name)
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration_seconds: Optional[float] = None

    def start(self):
        """Start the timer."""
        self.start_time = time.time()
        self.logger.info("Pipeline execution started.")

    def stop(self):
        """Stop the timer and calculate duration."""
        if self.start_time is None:
            raise RuntimeError("Timer has not been started. Call start() first.")
        
        self.end_time = time.time()
        self.duration_seconds = self.end_time - self.start_time
        self.logger.info("Pipeline execution stopped.")

    def report(self):
        """
        Log the final execution time to stdout and the dedicated log file.
        This is the critical artifact for SC-005.
        """
        if self.duration_seconds is None:
            self.stop()
            if self.duration_seconds is None:
                raise RuntimeError("Could not determine duration.")

        # Format the duration for readability
        hours, remainder = divmod(self.duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        formatted_duration = f"{int(hours)}h {int(minutes)}m {seconds:.2f}s"

        # Log to both stdout and file
        self.logger.info(f"Total Execution Time: {formatted_duration} ({self.duration_seconds:.2f} seconds)")
        
        # Explicitly print to stdout as a standalone line for easy parsing by CI/CD
        print(f"\n[SC-005 METRIC] Total Pipeline Duration: {formatted_duration} ({self.duration_seconds:.2f} seconds)\n")

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        self.report()
        # Do not suppress exceptions
        return False


if __name__ == "__main__":
    # Example usage for manual testing
    print("Testing RuntimeLogger utility...")
    with RuntimeLogger() as rl:
        time.sleep(1.5)  # Simulate work
        print("Simulating work...")
        time.sleep(0.5)
    
    print("Test complete. Check logs/runtime.log for details.")