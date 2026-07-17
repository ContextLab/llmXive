"""
Validation and runtime tracking module for llmXive pipeline.

Implements Constitution Principle VII: Execution time limits and
cumulative runtime tracking to prevent runaway processes.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from code.config import get_config, get_project_root

# Constants for runtime tracking
DEFAULT_TIMEOUT_SECONDS = 3600  # 1 hour default
LOG_FILE_NAME = "pipeline_log.json"


class RuntimeTracker:
    """
    Tracks cumulative runtime of the pipeline and enforces timeout limits.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the runtime tracker.

        Args:
            config: Optional configuration dictionary. If None, loads from code/config.py.
        """
        if config is None:
            config = get_config()

        self.timeout_seconds = config.get("execution_time_limit", DEFAULT_TIMEOUT_SECONDS)
        self.start_time: Optional[float] = None
        self.cumulative_time: float = 0.0
        self.log_file_path = Path(get_project_root()) / "data" / "interim" / LOG_FILE_NAME
        self._ensure_log_directory()
        self._load_existing_log()

    def _ensure_log_directory(self) -> None:
        """Ensure the directory for the log file exists."""
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_existing_log(self) -> None:
        """Load existing log data if the file exists."""
        if self.log_file_path.exists():
            try:
                with open(self.log_file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.cumulative_time = data.get("cumulative_time", 0.0)
            except (json.JSONDecodeError, IOError):
                # If log is corrupted, start fresh but warn
                self.cumulative_time = 0.0

    def start(self) -> None:
        """Start the timer for the current execution session."""
        self.start_time = time.time()
        self._log_event("session_start", {"timestamp": datetime.utcnow().isoformat()})

    def stop(self) -> float:
        """
        Stop the timer and update cumulative time.

        Returns:
            The duration of this session in seconds.
        """
        if self.start_time is None:
            raise RuntimeError("Timer was not started. Call start() first.")

        end_time = time.time()
        session_duration = end_time - self.start_time
        self.cumulative_time += session_duration
        self.start_time = None

        self._log_event("session_stop", {
            "timestamp": datetime.utcnow().isoformat(),
            "session_duration_seconds": session_duration,
            "cumulative_time_seconds": self.cumulative_time
        })

        return session_duration

    def check_limit(self) -> bool:
        """
        Check if the cumulative runtime has exceeded the limit.

        Returns:
            True if within limits, False if timeout exceeded.
        """
        current_total = self.cumulative_time
        if self.start_time is not None:
            current_total += (time.time() - self.start_time)

        is_within_limit = current_total <= self.timeout_seconds

        self._log_event("limit_check", {
            "timestamp": datetime.utcnow().isoformat(),
            "current_total_seconds": current_total,
            "limit_seconds": self.timeout_seconds,
            "is_within_limit": is_within_limit
        })

        return is_within_limit

    def get_remaining_time(self) -> float:
        """
        Get the remaining time before the timeout is triggered.

        Returns:
            Remaining seconds (0.0 if already exceeded).
        """
        current_total = self.cumulative_time
        if self.start_time is not None:
            current_total += (time.time() - self.start_time)

        remaining = self.timeout_seconds - current_total
        return max(0.0, remaining)

    def _log_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Append an event to the pipeline log file.

        Args:
            event_type: Type of event (e.g., 'session_start', 'limit_check').
            data: Dictionary of event data.
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": event_type,
            "data": data
        }

        try:
            with open(self.log_file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\n")
        except IOError as e:
            # Critical failure to log - raise to alert user
            raise RuntimeError(f"Failed to write to pipeline log: {e}") from e

    def trigger_timeout(self, reason: str = "Execution time limit exceeded") -> None:
        """
        Explicitly trigger a timeout abort.

        Args:
            reason: The reason for the timeout.
        """
        self._log_event("timeout_triggered", {
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "cumulative_time_seconds": self.cumulative_time
        })
        raise TimeoutError(f"{reason}. Cumulative time: {self.cumulative_time:.2f}s / {self.timeout_seconds}s")


# Global instance for convenience
_tracker: Optional[RuntimeTracker] = None


def get_tracker() -> RuntimeTracker:
    """
    Get or create the global runtime tracker instance.

    Returns:
        The RuntimeTracker instance.
    """
    global _tracker
    if _tracker is None:
        _tracker = RuntimeTracker()
    return _tracker


def start_pipeline_timer() -> None:
    """Start the global pipeline timer."""
    get_tracker().start()


def stop_pipeline_timer() -> float:
    """Stop the global pipeline timer and return session duration."""
    return get_tracker().stop()


def check_pipeline_limit() -> bool:
    """Check if the pipeline is still within time limits."""
    return get_tracker().check_limit()


def enforce_pipeline_limit() -> None:
    """
    Enforce the pipeline time limit. Raises TimeoutError if exceeded.
    """
    if not check_pipeline_limit():
        get_tracker().trigger_timeout()


# Context manager for automatic timer handling
class PipelineTimerContext:
    """Context manager for automatic timer start/stop and limit enforcement."""

    def __init__(self, enforce_limit: bool = True):
        """
        Args:
            enforce_limit: If True, checks limit on exit and raises if exceeded.
        """
        self.enforce_limit = enforce_limit
        self.tracker = get_tracker()

    def __enter__(self):
        self.tracker.start()
        return self.tracker

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.tracker.stop()
            if self.enforce_limit:
                enforce_pipeline_limit()
        except Exception:
            # Re-raise any exceptions from timing logic
            raise
        return False  # Don't suppress exceptions


def validate_data_integrity(
    self,
    data_path: str,
    required_columns: list,
    allow_nulls: bool = False
) -> Dict[str, Any]:
    """
    Basic data validation helper.

    Args:
        data_path: Path to the data file (CSV).
        required_columns: List of column names that must exist.
        allow_nulls: If False, flag rows with nulls in required columns.

    Returns:
        Dictionary with validation results.
    """
    import pandas as pd

    result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }

    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Failed to load data: {str(e)}")
        return result

    # Check columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        result["valid"] = False
        result["errors"].append(f"Missing required columns: {missing_cols}")

    # Check nulls
    if not allow_nulls and missing_cols == []:
        null_counts = df[required_columns].isnull().sum()
        null_cols = null_counts[null_counts > 0].index.tolist()
        if null_cols:
            result["valid"] = False
            result["errors"].append(f"Null values found in columns: {null_cols}")

    return result