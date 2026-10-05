"""
Validation and Runtime Guard (T006a, T006b).
Implements the active tracking loop for Constitution Principle VII.
"""
import json
import os
import time
import fcntl
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from config import get_config, compute_sha256

class RuntimeTracker:
    """
    Tracks cumulative pipeline runtime against the configured limit.
    Uses file-based locking to ensure thread/process safety.
    """
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.config = get_config()
        # Read MAX_RUNTIME_HOURS from config (T005)
        # The config stores total_pipeline_seconds, but T005 defined MAX_RUNTIME_HOURS = 6.
        # We will derive the limit in seconds from the config's timeout_total_pipeline_seconds
        # or default to 6 hours (21600 seconds) if not explicitly set in a way that matches T005.
        # Per T005: MAX_RUNTIME_HOURS = 6.
        self.max_runtime_seconds = 6 * 3600 
        
        # Ensure log file exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self._initialize_log()

    def _initialize_log(self):
        """Initialize the pipeline log with empty structure."""
        initial_data = {
            "stages": [],
            "total_elapsed_seconds": 0.0,
            "start_time": datetime.utcnow().isoformat(),
            "max_runtime_seconds": self.max_runtime_seconds
        }
        with open(self.log_path, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            json.dump(initial_data, f, indent=2)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def _load_log(self) -> Dict[str, Any]:
        """Load the current log state."""
        with open(self.log_path, 'r') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                return json.load(f)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def _save_log(self, data: Dict[str, Any]):
        """Save the log state."""
        with open(self.log_path, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            json.dump(data, f, indent=2)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def record_stage(self, stage_name: str, duration_seconds: float):
        """
        Record a completed stage and check the total runtime limit.
        This is the active logic for Constitution Principle VII.
        """
        current_log = self._load_log()
        
        # Update total elapsed time
        current_log['total_elapsed_seconds'] += duration_seconds
        current_log['stages'].append({
            "name": stage_name,
            "duration_seconds": duration_seconds,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Check against the limit (T006b Logic)
        if current_log['total_elapsed_seconds'] > self.max_runtime_seconds:
            raise TimeoutError(
                f"Constitution Principle VII Violation: "
                f"Cumulative runtime ({current_log['total_elapsed_seconds']:.2f}s) "
                f"exceeds limit ({self.max_runtime_seconds}s). Aborting pipeline."
            )
        
        self._save_log(current_log)

    def get_remaining_time(self) -> float:
        """Return remaining seconds before hard abort."""
        current_log = self._load_log()
        return max(0.0, self.max_runtime_seconds - current_log['total_elapsed_seconds'])

# Singleton instance
_tracker_instance: Optional[RuntimeTracker] = None

def get_tracker() -> RuntimeTracker:
    global _tracker_instance
    if _tracker_instance is None:
        config = get_config()
        log_path = config.paths['pipeline_log']
        _tracker_instance = RuntimeTracker(log_path)
    return _tracker_instance

def start_pipeline_timer():
    """Initialize the tracker if not already done."""
    get_tracker()

def stop_pipeline_timer():
    """No-op for now, as timing is handled per-stage."""
    pass

def check_pipeline_limit() -> bool:
    """
    Check if the pipeline is still within limits without recording a stage.
    Returns True if OK, False if limit exceeded.
    """
    tracker = get_tracker()
    current_log = tracker._load_log()
    return current_log['total_elapsed_seconds'] <= tracker.max_runtime_seconds

def enforce_pipeline_limit(stage_name: str, duration_seconds: float):
    """
    Record a stage and enforce the limit. Raises TimeoutError if exceeded.
    """
    tracker = get_tracker()
    tracker.record_stage(stage_name, duration_seconds)

def update_pipeline_log(stage_name: str, duration_seconds: float):
    """Alias for enforce_pipeline_limit to match main.py calls."""
    enforce_pipeline_limit(stage_name, duration_seconds)

class PipelineTimerContext:
    """Context manager to time a block and record it."""
    def __init__(self, stage_name: str):
        self.stage_name = stage_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        update_pipeline_log(self.stage_name, duration)
        return False

def validate_data_integrity(filepath: Path) -> bool:
    """
    Validate that a file exists and is non-empty (basic integrity check).
    """
    if not filepath.exists():
        return False
    if filepath.stat().st_size == 0:
        return False
    return True