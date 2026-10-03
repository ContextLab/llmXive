"""
Logging and runtime tracking infrastructure for the llmXive pipeline.
Implements Constitution Principle VII: Compute-time guard.
"""
import json
import os
import time
import fcntl
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent
LOG_FILE_PATH = PROJECT_ROOT / "data" / "results" / "pipeline_log.json"

# Configuration
MAX_RUNTIME_SECONDS = 6 * 3600  # 6 hours

class RuntimeTracker:
    """
    Tracks cumulative runtime of the pipeline and enforces the time limit.
    Writes state to data/results/pipeline_log.json.
    """
    def __init__(self, log_path: Optional[Path] = None):
        self.log_path = log_path or LOG_FILE_PATH
        self.start_time: Optional[float] = None
        self.elapsed_accumulated: float = 0.0
        self.stage_history: List[Dict[str, Any]] = []
        self._lock_file = None

    def _ensure_log_exists(self) -> None:
        """Ensure the log file and its directory exist."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            with open(self.log_path, 'w', encoding='utf-8') as f:
                json.dump({"stages": [], "total_elapsed_seconds": 0.0}, f, indent=2)

    def _load_log(self) -> Dict[str, Any]:
        """Load the current log state."""
        self._ensure_log_exists()
        with open(self.log_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_log(self, data: Dict[str, Any]) -> None:
        """Save log state with file locking for safety."""
        self._ensure_log_exists()
        with open(self.log_path, 'r+', encoding='utf-8') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EXCL)
            try:
                f.seek(0)
                f.truncate(0)
                f.write(json.dumps(data, indent=2))
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def start(self) -> None:
        """Start the timer for a stage."""
        if self.start_time is not None:
            raise RuntimeError("Timer already started. Call stop() first.")
        self.start_time = time.time()

    def stop(self, stage_name: str) -> float:
        """
        Stop the timer, record duration, and update the cumulative log.
        Returns the duration of the current stage.
        """
        if self.start_time is None:
            raise RuntimeError("Timer not started.")

        end_time = time.time()
        duration = end_time - self.start_time
        self.elapsed_accumulated += duration

        # Update log
        current_log = self._load_log()
        current_log["stages"].append({
            "name": stage_name,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
            "cumulative_seconds": self.elapsed_accumulated
        })
        current_log["total_elapsed_seconds"] = self.elapsed_accumulated

        self._save_log(current_log)

        # Reset state
        self.start_time = None
        return duration

    def check_limit(self) -> bool:
        """
        Check if cumulative runtime exceeds the limit.
        Returns True if limit is exceeded (should abort), False otherwise.
        """
        return self.elapsed_accumulated > MAX_RUNTIME_SECONDS

# Global instance for shared access
_global_tracker: Optional[RuntimeTracker] = None

def get_tracker() -> RuntimeTracker:
    """Get or create the global runtime tracker."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = RuntimeTracker()
    return _global_tracker

def start_pipeline_timer() -> None:
    """Start the global pipeline timer."""
    tracker = get_tracker()
    tracker.start()

def stop_pipeline_timer(stage_name: str) -> float:
    """Stop the global pipeline timer and record stage duration."""
    tracker = get_tracker()
    return tracker.stop(stage_name)

def check_pipeline_limit() -> bool:
    """Check if the global pipeline has exceeded the time limit."""
    tracker = get_tracker()
    return tracker.check_limit()

def enforce_pipeline_limit() -> None:
    """
    Enforce the time limit. Raises TimeoutError if exceeded.
    """
    if check_pipeline_limit():
        tracker = get_tracker()
        raise TimeoutError(
            f"Pipeline execution time limit exceeded. "
            f"Accumulated time: {tracker.elapsed_accumulated:.2f}s > {MAX_RUNTIME_SECONDS}s"
        )

def update_pipeline_log(stage_name: str, status: str = "completed", error: Optional[str] = None) -> None:
    """
    Update the pipeline log with a new entry for a stage.
    This is a convenience wrapper for manual logging if not using the timer.
    """
    tracker = get_tracker()
    tracker._ensure_log_exists()
    log_data = tracker._load_log()
    
    entry = {
        "name": stage_name,
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "duration_seconds": tracker.elapsed_accumulated, # Approximate if not timed
        "cumulative_seconds": tracker.elapsed_accumulated
    }
    if error:
        entry["error"] = error

    log_data["stages"].append(entry)
    tracker._save_log(log_data)

class PipelineTimerContext:
    """Context manager for timing a pipeline stage."""
    def __init__(self, stage_name: str):
        self.stage_name = stage_name
        self.duration: Optional[float] = None

    def __enter__(self):
        tracker = get_tracker()
        tracker.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        tracker = get_tracker()
        if exc_type is None:
            self.duration = tracker.stop(self.stage_name)
        else:
            # Record failure but don't stop timer accumulation if we want to track total time even on error
            # Or stop timer? Usually we stop tracking this specific stage.
            tracker.start_time = None # Reset without saving duration
        return False

def validate_data_integrity(file_path: Path) -> bool:
    """
    Simple validation to ensure a file exists and is not empty.
    Returns True if valid, False otherwise.
    """
    if not file_path.exists():
        return False
    if file_path.stat().st_size == 0:
        return False
    return True
