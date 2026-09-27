"""
Validation infrastructure (T006).
Implements the logging mechanism and file handles required for runtime tracking
against the execution time limit (Constitution Principle VII).
Parallel-safe initialization and logging to data/results/pipeline_log.json.
"""
import json
import os
import time
import fcntl
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure the output directory exists
RESULTS_DIR = Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = RESULTS_DIR / "pipeline_log.json"

# Configuration
MAX_RUNTIME_SECONDS = 3600  # Default 1 hour limit, configurable via env if needed

class RuntimeTracker:
    """
    Tracks cumulative pipeline runtime.
    Uses file locking for parallel safety when appending to the log.
    """
    def __init__(self):
        self.start_time: Optional[float] = None
        self.log_path = str(LOG_FILE)
        # Initialize the log file if it doesn't exist
        self._ensure_log_initialized()

    def _ensure_log_initialized(self):
        """
        Ensures the log file exists. If it's empty or missing, initializes it.
        This satisfies the requirement to "initialize the logging mechanism".
        """
        if not os.path.exists(self.log_path):
            with open(self.log_path, 'w') as f:
                # Initialize as an empty JSON lines file or a JSON array start
                # Using JSON Lines format for streaming appends
                f.write("") 

    def start(self):
        """Start the timer."""
        self.start_time = time.time()

    def stop(self, stage_name: str = "pipeline"):
        """
        Stop the timer and log the cumulative runtime.
        Uses file locking (fcntl) to ensure parallel safety.
        """
        if self.start_time is None:
            raise RuntimeError("Timer was not started. Call start() first.")
        
        elapsed = time.time() - self.start_time
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'stage': stage_name,
            'cumulative_seconds': round(elapsed, 2),
            'status': 'completed'
        }
        
        # Parallel-safe append using file locking
        with open(self.log_path, 'a') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.write(json.dumps(log_entry) + '\n')
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        
        self.start_time = None
        return elapsed

    def check_limit(self) -> bool:
        """
        Checks if the current cumulative runtime exceeds the limit.
        Returns True if within limit, False if exceeded.
        """
        if self.start_time is None:
            return True
        
        elapsed = time.time() - self.start_time
        return elapsed <= MAX_RUNTIME_SECONDS

# Global singleton instance
_tracker: Optional[RuntimeTracker] = None

def get_tracker() -> RuntimeTracker:
    global _tracker
    if _tracker is None:
        _tracker = RuntimeTracker()
    return _tracker

def start_pipeline_timer():
    """Start the global pipeline timer."""
    tracker = get_tracker()
    tracker.start()

def stop_pipeline_timer(stage_name: str = "pipeline"):
    """Stop the global pipeline timer and log the result."""
    tracker = get_tracker()
    tracker.stop(stage_name)

def check_pipeline_limit() -> bool:
    """Check if the pipeline is within the time limit."""
    tracker = get_tracker()
    return tracker.check_limit()

def enforce_pipeline_limit():
    """
    Enforce the time limit. If exceeded, raises a RuntimeError.
    This is the active enforcement mechanism.
    """
    tracker = get_tracker()
    if not tracker.check_limit():
        raise RuntimeError(
            f"Pipeline execution time limit exceeded. "
            f"Current runtime: {time.time() - tracker.start_time:.2f}s > {MAX_RUNTIME_SECONDS}s"
        )

class PipelineTimerContext:
    """Context manager for timing a specific block."""
    def __init__(self, stage_name: str = "block"):
        self.stage_name = stage_name
        self.tracker = get_tracker()

    def __enter__(self):
        self.tracker.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.tracker.stop(self.stage_name)
        return False

def validate_data_integrity():
    """
    Placeholder for data integrity checks.
    To be implemented in later tasks if needed.
    """
    pass
