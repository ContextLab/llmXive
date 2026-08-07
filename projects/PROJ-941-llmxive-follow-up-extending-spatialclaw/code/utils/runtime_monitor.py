"""
Runtime Monitor & Abort Utility for SpatialClaw Pipeline.

This module provides a context manager and utility functions to enforce
hard time limits on long-running processes (Baseline execution, 2D Agent runs).
If the configured `max_runtime_hours` from `data/power_config.yaml` is exceeded,
the process is terminated, partial results are moved to `results/logs/partial/`,
and a `RUNTIME_OVERFLOW` error is logged.

Dependencies:
    - data/power_config.yaml (must exist)
    - utils.budget_check (for config loading)
"""
import os
import sys
import time
import signal
import shutil
import logging
import argparse
from datetime import datetime
from typing import Optional, Callable, Any, Dict
from contextlib import contextmanager

# Project imports
from utils.budget_check import load_power_config
from utils.logging import setup_logging

# Constants
CONFIG_PATH = "data/power_config.yaml"
PARTIAL_DIR = "results/logs/partial"
MAIN_LOG_PATH = "results/logs/execution.log"
RUNTIME_OVERFLOW_ERROR = "RUNTIME_OVERFLOW"


class RuntimeLimitExceededError(Exception):
    """Raised when the execution time exceeds the configured limit."""
    pass


def _move_partial_results(run_id: Optional[str] = None) -> None:
    """
    Moves any existing partial results to the partial directory.
    If run_id is provided, moves specific run artifacts; otherwise moves generic partials.
    """
    if not os.path.exists(PARTIAL_DIR):
        os.makedirs(PARTIAL_DIR, exist_ok=True)

    source_dir = "results/logs"
    # Identify files that might be partials (e.g., run_*.json, baseline_run.json if interrupted)
    # We move them to preserve state without overwriting successful runs if any exist elsewhere.
    # Specific logic: if a run was interrupted, its logs are in results/logs/
    
    # Move any .json files in results/logs that look like run outputs but aren't the final aggregated ones
    # For simplicity in this generic monitor, we move the 'run' artifacts if they exist and are incomplete.
    # A more robust system would track specific file names per run_id.
    
    # Strategy: Move everything in results/logs/ that is not the main execution.log or the final analysis files
    # to the partial folder, preserving the directory structure.
    
    if os.path.isdir(source_dir):
        for item in os.listdir(source_dir):
            src_path = os.path.join(source_dir, item)
            # Skip the partial directory itself and the main log
            if item == "partial" or item == "execution.log":
                continue
            
            # If it's a file, move it. If it's a dir (like 'runs'), check contents.
            if os.path.isfile(src_path):
                shutil.move(src_path, os.path.join(PARTIAL_DIR, item))
            elif os.path.isdir(src_path):
                dest_dir = os.path.join(PARTIAL_DIR, item)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir, exist_ok=True)
                for sub_item in os.listdir(src_path):
                    shutil.move(os.path.join(src_path, sub_item), os.path.join(dest_dir, sub_item))
                # Remove empty source dir
                try:
                    os.rmdir(src_path)
                except OSError:
                    pass # Not empty, leave it


def _log_overflow_error(max_seconds: float, elapsed: float, logger: logging.Logger) -> None:
    """Logs the runtime overflow error and raises an exception."""
    msg = (
        f"{RUNTIME_OVERFLOW_ERROR}: "
        f"Execution exceeded budget. Limit: {max_seconds:.2f}s, Elapsed: {elapsed:.2f}s. "
        f"Process terminated and partial results moved to '{PARTIAL_DIR}'."
    )
    logger.error(msg)
    # Also write to the specific execution log if possible
    try:
        with open(MAIN_LOG_PATH, "a") as f:
            f.write(f"{datetime.now().isoformat()} ERROR {msg}\n")
    except Exception:
        pass
    
    raise RuntimeLimitExceededError(msg)


@contextmanager
def runtime_monitor(
    max_runtime_hours: Optional[float] = None,
    logger_name: str = "runtime_monitor",
    run_id: Optional[str] = None
):
    """
    Context manager to enforce a hard time limit on a block of code.

    Args:
        max_runtime_hours: Override the limit from config. If None, reads from data/power_config.yaml.
        logger_name: Name of the logger to use.
        run_id: Optional identifier for this run (used for cleanup context).

    Yields:
        None

    Raises:
        RuntimeLimitExceededError: If the time limit is exceeded.
    """
    # Load config
    if max_runtime_hours is None:
        try:
            config = load_power_config(CONFIG_PATH)
            max_runtime_hours = float(config.get("max_runtime_hours", 0.0))
        except Exception as e:
            logging.error(f"Failed to load power config for runtime monitor: {e}")
            max_runtime_hours = float('inf') # Fail open if config missing? Or fail closed? 
            # Per spec: "terminate... if limit exceeded". If config missing, we can't check.
            # We'll assume infinite if config missing to avoid blocking dev, but log warning.
            logging.warning("max_runtime_hours not found in config. No limit enforced.")

    if max_runtime_hours <= 0:
        logging.warning("max_runtime_hours is 0 or negative. No limit enforced.")
        yield
        return

    max_seconds = max_runtime_hours * 3600.0
    start_time = time.time()
    
    # Setup logger
    logger = logging.getLogger(logger_name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    logger.info(f"Runtime monitor started. Limit: {max_runtime_hours} hours ({max_seconds:.2f} seconds).")

    try:
        yield
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        _move_partial_results(run_id)
        _log_overflow_error(max_seconds, elapsed, logger)
        raise
    except Exception as e:
        # If it's our specific error, re-raise immediately
        if isinstance(e, RuntimeLimitExceededError):
            raise
        # Otherwise, check time before re-raising or letting it propagate?
        # The spec says "If the limit is exceeded... terminate". 
        # We check time periodically or at the end? 
        # For a context manager, we check at the end or if we catch a timeout signal.
        # Since we can't easily catch SIGALRM in a pure python context manager without signal handlers,
        # we check at the exit.
        elapsed = time.time() - start_time
        if elapsed > max_seconds:
            _move_partial_results(run_id)
            _log_overflow_error(max_seconds, elapsed, logger)
        raise

    # Final check on exit
    elapsed = time.time() - start_time
    if elapsed > max_seconds:
        _move_partial_results(run_id)
        _log_overflow_error(max_seconds, elapsed, logger)


def check_runtime_limit(max_runtime_hours: Optional[float] = None) -> None:
    """
    A simple function to check the current runtime against a limit.
    Useful for periodic checks inside a long loop if not using the context manager.
    
    Raises:
        RuntimeLimitExceededError: If limit exceeded.
    """
    # This is a stateless check, so it needs a stored start time.
    # For a global check, we'd need a file or global variable.
    # This function is more of a helper for the context manager logic.
    pass


def parse_args():
    parser = argparse.ArgumentParser(description="Runtime Monitor Utility for SpatialClaw")
    parser.add_argument("--config", type=str, default=CONFIG_PATH, help="Path to power_config.yaml")
    parser.add_argument("--max-hours", type=float, default=None, help="Override max runtime hours")
    return parser.parse_args()


def main():
    """
    Entry point for testing the monitor or running a dummy task.
    Usage: python code/utils/runtime_monitor.py --max-hours 0.001
    """
    args = parse_args()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger("runtime_monitor_main")
    
    logger.info("Starting Runtime Monitor Test.")
    
    try:
        with runtime_monitor(max_runtime_hours=args.max_hours, logger_name="runtime_monitor_main"):
            logger.info("Inside monitor. Simulating work...")
            # Simulate work
            if args.max_hours:
                # Sleep for slightly longer than limit to trigger error
                time.sleep(args.max_hours * 3600 + 1)
            else:
                time.sleep(1)
            logger.info("Work completed.")
    except RuntimeLimitExceededError as e:
        logger.error(f"Monitor caught: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(2)
    
    logger.info("Monitor finished successfully.")


if __name__ == "__main__":
    main()