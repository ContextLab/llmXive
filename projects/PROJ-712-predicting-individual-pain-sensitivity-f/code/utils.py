"""
Utility functions for the pain sensitivity prediction pipeline.
Implements Constitution Principles V (Reproducibility) and III (Verified Accuracy).
"""
import hashlib
import logging
import os
import random
import time
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

# Import configuration constants
try:
    from config import MAX_EXECUTION_SECONDS, STATE_FILE, STATE_DIR
except ImportError:
    # Fallback for direct execution or different import context
    MAX_EXECUTION_SECONDS = 6 * 3600
    STATE_FILE = Path("state/projects/PROJ-712-predicting-individual-pain-sensitivity-f.yaml")
    STATE_DIR = Path("state/projects")


def set_global_seed(seed: int = 42) -> None:
    """
    Set the global random seed for reproducibility.
    Affects Python's random, NumPy (if imported), and other libraries.
    """
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    logging.info(f"Global seed set to {seed}")


def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """
    Configure the root logger with a standard format.
    Returns the configured logger instance.
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            # Optionally add file handler if needed
            # logging.FileHandler("pipeline.log")
        ]
    )
    return logging.getLogger(__name__)


def compute_checksum(file_path: str | Path) -> str:
    """
    Compute the SHA-256 checksum of a file.
    Reads the file in chunks to handle large files efficiently.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def compute_file_hash(file_path: str | Path) -> str:
    """
    Alias for compute_checksum for consistency with naming conventions.
    """
    return compute_checksum(file_path)


def record_artifact_hash(
    artifact_name: str,
    file_path: str | Path,
    state_file: Optional[str | Path] = None
) -> None:
    """
    Record the hash of an artifact into the project state YAML file.
    Creates the state file and directory if they do not exist.
    """
    if state_file is None:
        state_file = STATE_FILE

    state_path = Path(state_file)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing state or initialize
    if state_path.exists():
        with open(state_path, "r") as f:
            state_data = yaml.safe_load(f) or {}
    else:
        state_data = {"artifacts": {}}

    if "artifacts" not in state_data:
        state_data["artifacts"] = {}

    # Compute hash
    file_hash = compute_file_hash(file_path)

    # Update state
    state_data["artifacts"][artifact_name] = {
        "path": str(file_path),
        "sha256": file_hash,
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    # Write back
    with open(state_path, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

    logging.info(f"Recorded artifact hash for {artifact_name}: {file_hash}")


# Timing Instrumentation for SC-005
_start_time: Optional[float] = None
_timer_running: bool = False


def get_current_timestamp() -> str:
    """Return current UTC timestamp in ISO format."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def measure_duration(start_time: float, end_time: Optional[float] = None) -> float:
    """
    Calculate the duration in seconds between start_time and end_time.
    If end_time is not provided, uses the current time.
    """
    if end_time is None:
        end_time = time.time()
    return end_time - start_time


def assert_duration_limit(duration_seconds: float, limit_seconds: Optional[float] = None) -> None:
    """
    Assert that the execution duration is within the allowed limit.
    SC-005: Execution must complete within 6 hours.
    Raises AssertionError if the limit is exceeded.
    """
    if limit_seconds is None:
        limit_seconds = MAX_EXECUTION_SECONDS

    limit_hours = limit_seconds / 3600
    duration_hours = duration_seconds / 3600

    if duration_seconds > limit_seconds:
        msg = (
            f"SC-005 VIOLATION: Execution time ({duration_hours:.2f} hours) "
            f"exceeds the maximum allowed limit ({limit_hours:.2f} hours). "
            f"Duration: {duration_seconds:.2f} seconds. Limit: {limit_seconds:.2f} seconds."
        )
        logging.error(msg)
        raise AssertionError(msg)
    
    logging.info(f"Duration check passed: {duration_hours:.2f} hours < {limit_hours:.2f} hours limit.")


def validate_pipeline_duration(start_time: float) -> None:
    """
    Convenience function to measure duration from a start time and assert the limit.
    Raises AssertionError if the limit is exceeded.
    """
    duration = measure_duration(start_time)
    assert_duration_limit(duration)


def start_timer() -> float:
    """
    Start the global pipeline timer.
    Returns the start timestamp.
    """
    global _start_time, _timer_running
    _start_time = time.time()
    _timer_running = True
    logging.info(f"Pipeline timer started at {get_current_timestamp()}")
    return _start_time


def stop_timer() -> float:
    """
    Stop the global pipeline timer and return the total duration.
    Raises AssertionError if the duration exceeds the limit (SC-005).
    """
    global _start_time, _timer_running
    if _start_time is None:
        raise RuntimeError("Timer was not started. Call start_timer() first.")
    
    end_time = time.time()
    duration = end_time - _start_time
    _timer_running = False
    
    logging.info(f"Pipeline timer stopped. Total duration: {duration:.2f} seconds")
    
    # Enforce SC-005
    assert_duration_limit(duration)
    
    return duration
