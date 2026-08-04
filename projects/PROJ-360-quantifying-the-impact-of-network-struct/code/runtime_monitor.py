"""
Runtime monitoring and pipeline instrumentation.

This module provides utilities to measure and log the total pipeline runtime
to verify compliance with SC-005 (pipeline must complete in < 6 hours).

It acts as a wrapper script that enforces a timeout during execution.
"""

import os
import time
import logging
import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, List

# Constants
RESULTS_DIR = Path("results")
RUNTIME_LOG_PATH = RESULTS_DIR / "runtime_log.json"
START_TIME_MARKER_PATH = RESULTS_DIR / ".pipeline_start_time"
MAX_RUNTIME_HOURS = 6
MAX_RUNTIME_SECONDS = MAX_RUNTIME_HOURS * 3600

# Default pipeline command to wrap
DEFAULT_PIPELINE_CMD = [
    sys.executable, "code/quickstart.py"
]

def setup_runtime_logger(name: str = "runtime_monitor") -> logging.Logger:
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
    file_handler = logging.FileHandler(RESULTS_DIR / "runtime_monitor.log")
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler for immediate feedback
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

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

def run_pipeline_with_timeout(cmd: List[str], timeout_seconds: int) -> int:
    """
    Run the pipeline command with a hard timeout.

    Args:
        cmd: Command and arguments to execute
        timeout_seconds: Maximum allowed runtime in seconds

    Returns:
        Exit code: 0 if successful, 1 if timeout or error
    """
    logger = setup_runtime_logger()
    start_time = time.time()
    
    # Record start time if not already done
    if not START_TIME_MARKER_PATH.exists():
        record_start_time()

    logger.info(f"Starting pipeline: {' '.join(cmd)}")
    logger.info(f"Timeout limit: {timeout_seconds} seconds ({timeout_seconds/3600:.2f} hours)")

    try:
        # Run the subprocess
        process = subprocess.run(
            cmd,
            timeout=timeout_seconds,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=Path.cwd()
        )

        end_time = time.time()
        elapsed_seconds = end_time - start_time
        elapsed_hours = elapsed_seconds / 3600

        # Log the output (truncated if too long)
        if process.stdout:
            stdout_lines = process.stdout.split('\n')
            for line in stdout_lines[-50:]: # Log last 50 lines
                logger.info(line)
            if len(stdout_lines) > 50:
                logger.info(f"... ({len(stdout_lines) - 50} more lines suppressed)")

        # Record runtime metrics
        runtime_data = {
            "start_timestamp": datetime.fromtimestamp(load_pipeline_start_time() or start_time).isoformat(),
            "end_timestamp": datetime.now().isoformat(),
            "elapsed_seconds": elapsed_seconds,
            "elapsed_hours": elapsed_hours,
            "max_allowed_hours": MAX_RUNTIME_HOURS,
            "timed_out": False,
            "exit_code": process.returncode,
            "compliant": elapsed_seconds <= MAX_RUNTIME_SECONDS
        }

        # Write to JSON log
        with open(RUNTIME_LOG_PATH, 'w') as f:
            json.dump(runtime_data, f, indent=2)

        logger.info(f"Pipeline finished. Exit code: {process.returncode}")
        logger.info(f"Total runtime: {elapsed_seconds:.2f} seconds ({elapsed_hours:.4f} hours)")

        if process.returncode != 0:
            logger.error(f"Pipeline failed with exit code {process.returncode}")
            return 1

        # Check timeout compliance
        if elapsed_seconds > MAX_RUNTIME_SECONDS:
            error_msg = "ERROR: Runtime exceeds time limit"
            logger.error(error_msg)
            logger.error(f"Runtime {elapsed_seconds}s > {MAX_RUNTIME_SECONDS}s limit")
            return 1

        logger.info("SC-005 Compliance Check: PASSED")
        return 0

    except subprocess.TimeoutExpired:
        end_time = time.time()
        elapsed_seconds = end_time - start_time
        
        error_msg = "ERROR: Runtime exceeds time limit"
        logger.error(error_msg)
        logger.error(f"Pipeline exceeded {timeout_seconds}s ({timeout_seconds/3600:.2f}h) limit after {elapsed_seconds:.2f}s")
        
        # Record timeout in log
        runtime_data = {
            "start_timestamp": datetime.fromtimestamp(load_pipeline_start_time() or start_time).isoformat(),
            "end_timestamp": datetime.now().isoformat(),
            "elapsed_seconds": elapsed_seconds,
            "max_allowed_hours": MAX_RUNTIME_HOURS,
            "timed_out": True,
            "exit_code": -1,
            "compliant": False,
            "error": "Runtime exceeds time limit"
        }
        
        with open(RUNTIME_LOG_PATH, 'w') as f:
            json.dump(runtime_data, f, indent=2)

        return 1
    except Exception as e:
        logger.error(f"Unexpected error during pipeline execution: {e}")
        return 1

def main() -> int:
    """
    Main entry point for runtime monitor wrapper script.

    Usage:
        python code/runtime_monitor.py [command] [args...]
    
    If no command is provided, it defaults to running the quickstart pipeline.
    
    Returns:
        Exit code (0 for success, 1 for failure/timeout)
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Runtime monitor wrapper for the pipeline. Enforces SC-005 timeout."
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=MAX_RUNTIME_SECONDS,
        help=f"Timeout in seconds (default: {MAX_RUNTIME_SECONDS} seconds / {MAX_RUNTIME_HOURS} hours)"
    )
    parser.add_argument(
        "--command",
        nargs=argparse.REMAINDER,
        help="Command to run. Defaults to 'python code/quickstart.py'"
    )

    args = parser.parse_args()

    # Determine command to run
    if args.command:
        cmd = args.command
    else:
        cmd = DEFAULT_PIPELINE_CMD

    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    return run_pipeline_with_timeout(cmd, args.timeout)

if __name__ == "__main__":
    exit(main())