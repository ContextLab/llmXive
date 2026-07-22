"""
Timeout utility for per-sample execution limits.

This module provides a wrapper function to enforce a maximum execution time
for individual samples in a pipeline. If a sample exceeds the timeout,
the specific sample_id and duration are logged to a JSON file, and a
sentinel value is returned to allow the pipeline to continue without
aborting the entire process.
"""

import json
import signal
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional

# Ensure the log directory exists
LOG_DIR = Path("data/processed")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "timeout_log.json"


class TimeoutError(Exception):
    """Custom exception for per-sample timeouts."""
    pass


def _timeout_handler(signum, frame):
    """Signal handler for the timeout alarm."""
    raise TimeoutError("Sample execution exceeded the time limit.")


def with_timeout(timeout_seconds: float, sample_id: str) -> Callable:
    """
    Decorator factory that wraps a function to enforce a per-sample timeout.

    Args:
        timeout_seconds: Maximum allowed execution time in seconds.
        sample_id: Identifier for the current sample being processed.

    Returns:
        A decorator that wraps the target function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            result = None

            # Set up the signal handler for the timeout
            # Note: signal.alarm only works on Unix-like systems.
            # For cross-platform compatibility in a broader context,
            # a threading-based approach might be preferred, but signal
            # is the standard for strict timeouts in Python scripts.
            try:
                old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
                signal.alarm(int(timeout_seconds))

                try:
                    result = func(*args, **kwargs)
                finally:
                    # Cancel the alarm
                    signal.alarm(0)
                    # Restore the old handler
                    signal.signal(signal.SIGALRM, old_handler)

            except TimeoutError:
                elapsed = time.time() - start_time
                _log_timeout(sample_id, elapsed, func.__name__)
                return None  # Sentinel value

            except Exception as e:
                # Re-raise unexpected errors immediately
                raise e

            return result

        return wrapper
    return decorator


def _log_timeout(sample_id: str, duration: float, func_name: str) -> None:
    """
    Logs a timeout event to the JSON log file.

    Args:
        sample_id: The ID of the timed-out sample.
        duration: The time elapsed before the timeout.
        func_name: The name of the function that timed out.
    """
    entry = {
        "sample_id": sample_id,
        "function": func_name,
        "duration_seconds": duration,
        "timeout_limit": None, # Will be updated if we want to store the limit
        "timestamp": time.strftime("%Y-%m-%dT%H-%M-%S", time.gmtime())
    }

    # Read existing logs if present
    logs = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except (json.JSONDecodeError, IOError):
            logs = []

    logs.append(entry)

    # Write back to file
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=2)


def timeout_wrapper(func: Callable, timeout_seconds: float, sample_id: str) -> Callable:
    """
    Functional wrapper equivalent to the decorator factory.

    Args:
        func: The function to wrap.
        timeout_seconds: Maximum allowed execution time.
        sample_id: Identifier for the sample.

    Returns:
        The wrapped function.
    """
    return with_timeout(timeout_seconds, sample_id)(func)
