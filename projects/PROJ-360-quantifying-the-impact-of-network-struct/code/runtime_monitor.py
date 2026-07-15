"""
Runtime monitoring and instrumentation for the pipeline.

This module provides utilities to measure total pipeline runtime,
log elapsed time to results/runtime.log, and assert compliance
with the 6-hour limit (SC-005).
"""

import os
import time
import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

# Constants
SIX_HOURS_SECONDS = 6 * 60 * 60
RESULTS_DIR = Path("results")
RUNTIME_LOG_PATH = RESULTS_DIR / "runtime.log"
START_TIME_MARKER_PATH = RESULTS_DIR / ".pipeline_start_time"


def setup_runtime_logger() -> logging.Logger:
    """Set up and return the runtime logger."""
    logger = logging.getLogger("runtime_monitor")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def record_start_time() -> None:
    """
    Record the current pipeline start time to a marker file.
    This should be called at the very beginning of the pipeline.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    start_time = time.time()
    with open(START_TIME_MARKER_PATH, "w") as f:
        f.write(str(start_time))


def load_pipeline_start_time() -> Optional[float]:
    """
    Load the pipeline start time from the marker file.
    Returns None if the file does not exist.
    """
    if not START_TIME_MARKER_PATH.exists():
        return None
    with open(START_TIME_MARKER_PATH, "r") as f:
        return float(f.read().strip())


def measure_and_log_runtime() -> float:
    """
    Measure elapsed time since pipeline start, log to runtime.log,
    and assert compliance with the 6-hour limit.

    Returns:
        float: Elapsed time in seconds.

    Raises:
        RuntimeError: If elapsed time exceeds 6 hours.
    """
    logger = setup_runtime_logger()

    start_time = load_pipeline_start_time()
    if start_time is None:
        logger.error("Pipeline start time not found. Ensure record_start_time() was called.")
        raise RuntimeError("Pipeline start time not found.")

    end_time = time.time()
    elapsed_seconds = end_time - start_time
    elapsed_hours = elapsed_seconds / 3600

    # Log to runtime.log
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()

    log_entry = {
        "timestamp": timestamp,
        "elapsed_seconds": elapsed_seconds,
        "elapsed_hours": elapsed_hours,
        "start_time_iso": datetime.fromtimestamp(start_time).isoformat(),
        "end_time_iso": timestamp,
        "compliance_status": "PASS" if elapsed_seconds <= SIX_HOURS_SECONDS else "FAIL"
    }

    with open(RUNTIME_LOG_PATH, "w") as f:
        json.dump(log_entry, f, indent=2)

    logger.info(f"Pipeline runtime: {elapsed_hours:.2f} hours ({elapsed_seconds:.2f} seconds)")

    # Assert compliance with SC-005
    if elapsed_seconds > SIX_HOURS_SECONDS:
        error_msg = f"Pipeline exceeded 6-hour limit (SC-005). Elapsed: {elapsed_hours:.2f} hours."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    logger.info("Compliance with SC-005 (6-hour limit) verified.")
    return elapsed_seconds


def main() -> None:
    """
    Entry point for runtime monitoring.
    Measures elapsed time, logs it, and checks compliance.
    """
    logger = setup_runtime_logger()
    logger.info("Starting runtime measurement...")

    try:
        elapsed = measure_and_log_runtime()
        logger.info(f"Runtime measurement complete: {elapsed:.2f} seconds")
    except RuntimeError as e:
        logger.error(str(e))
        raise


if __name__ == "__main__":
    main()
