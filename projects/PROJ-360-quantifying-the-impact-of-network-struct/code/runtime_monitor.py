"""
Runtime monitoring and pipeline instrumentation.

This module provides utilities to measure and log the total pipeline runtime
to verify compliance with SC-005 (pipeline must complete in < 6 hours).
"""

import os
import time
import logging
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Constants
RESULTS_DIR = Path("results")
RUNTIME_LOG_PATH = RESULTS_DIR / "runtime.log"
START_TIME_MARKER_PATH = RESULTS_DIR / ".pipeline_start_time"
MAX_RUNTIME_HOURS = 6
MAX_RUNTIME_SECONDS = MAX_RUNTIME_HOURS * 3600

def setup_runtime_logger(name: str = "runtime") -> logging.Logger:
    """
    Setup a dedicated logger for runtime monitoring.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # File handler
    file_handler = logging.FileHandler(RUNTIME_LOG_PATH)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

def record_start_time() -> None:
    """
    Record the pipeline start time to a marker file.
    This should be called at the very beginning of the pipeline.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    start_time = time.time()
    timestamp = datetime.now().isoformat()

    with open(START_TIME_MARKER_PATH, 'w') as f:
        json.dump({
            "start_timestamp": timestamp,
            "start_epoch": start_time
        }, f)

    logger = setup_runtime_logger()
    logger.info(f"Pipeline started at {timestamp}")

def load_pipeline_start_time() -> Optional[float]:
    """
    Load the pipeline start time from the marker file.

    Returns:
        Start time in epoch seconds, or None if not found
    """
    if not START_TIME_MARKER_PATH.exists():
        return None

    try:
        with open(START_TIME_MARKER_PATH, 'r') as f:
            data = json.load(f)
            return data.get("start_epoch")
    except (json.JSONDecodeError, IOError):
        return None

def measure_and_log_runtime() -> bool:
    """
    Measure total pipeline runtime, log it, and assert compliance with SC-005.

    Returns:
        True if runtime is within limits, False otherwise

    Raises:
        RuntimeError: If runtime exceeds the 6-hour limit
    """
    logger = setup_runtime_logger()
    start_epoch = load_pipeline_start_time()

    if start_epoch is None:
        logger.warning("No start time marker found. Assuming immediate start.")
        start_epoch = time.time()

    end_epoch = time.time()
    elapsed_seconds = end_epoch - start_epoch
    elapsed_hours = elapsed_seconds / 3600

    # Log format requirement: "Total runtime: <X> seconds"
    log_message = f"Total runtime: {elapsed_seconds} seconds"
    
    # Append to log file
    with open(RUNTIME_LOG_PATH, 'a') as f:
        f.write(f"{log_message}\n")
        f.write(f"Start Epoch: {start_epoch}\n")
        f.write(f"End Epoch: {end_epoch}\n")
        f.write(f"Elapsed Time: {elapsed_seconds:.2f} seconds ({elapsed_hours:.4f} hours)\n")
        f.write(f"Max Allowed: {MAX_RUNTIME_HOURS} hours\n")
        f.write(f"Compliant: {elapsed_seconds <= MAX_RUNTIME_SECONDS}\n")
        f.write("-" * 40 + "\n")

    logger.info(log_message)
    logger.info(f"SC-005 Compliance Check: {'PASSED' if elapsed_seconds <= MAX_RUNTIME_SECONDS else 'FAILED'}")

    if elapsed_seconds > MAX_RUNTIME_SECONDS:
        error_msg = f"ERROR: Runtime {elapsed_seconds}s exceeds 6h limit"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    return True

def main() -> int:
    """
    Main entry point for runtime monitoring script.

    This script can be run standalone to:
    1. Record the start time (if called with --record-start)
    2. Measure and log the total runtime (default behavior)

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    import argparse

    parser = argparse.ArgumentParser(description="Pipeline runtime monitor")
    parser.add_argument(
        "--record-start",
        action="store_true",
        help="Record the pipeline start time"
    )
    parser.add_argument(
        "--measure",
        action="store_true",
        help="Measure and log the total runtime (default)"
    )

    args = parser.parse_args()

    try:
        if args.record_start:
            record_start_time()
            print("Start time recorded.")
            return 0
        else:
            measure_and_log_runtime()
            print("Runtime measured and logged successfully.")
            return 0
    except RuntimeError as e:
        # Explicitly exit with code 1 on timeout as per SC-005
        print(f"Runtime compliance check failed: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())