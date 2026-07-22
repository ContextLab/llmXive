"""
Timeout utility for per-sample execution limits.

Implements a wrapper that enforces a time limit on callable execution,
logs failures to a JSON file, and returns a sentinel value instead of
raising an exception that would abort the parent process.
"""

import json
import signal
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional


# Configuration
LOG_DIR = Path("data/processed")
LOG_FILE = LOG_DIR / "timeout_log.json"


class TimeoutError(Exception):
    """Custom exception for timeout events."""
    pass


def _log_timeout(sample_id: str, duration: float, error_msg: str = None) -> None:
    """
    Appends a timeout record to the persistent JSON log file.
    Creates the log file and directory if they do not exist.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    record = {
        "sample_id": sample_id,
        "duration_seconds": duration,
        "error_message": error_msg,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    existing_records = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    existing_records = json.loads(content)
                if not isinstance(existing_records, list):
                    existing_records = [existing_records]
        except (json.JSONDecodeError, IOError):
            existing_records = []

    existing_records.append(record)

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_records, f, indent=2)


def with_timeout(timeout_seconds: float) -> Callable:
    """
    Decorator factory that creates a timeout wrapper for a function.

    Args:
        timeout_seconds: Maximum allowed execution time in seconds.

    Returns:
        A decorator that wraps the target function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            sample_id = kwargs.get("sample_id") or args[0] if args else "unknown"
            result = None

            def handler(signum, frame):
                raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds}s")

            # Set the signal handler
            old_handler = signal.signal(signal.SIGALRM, handler)
            signal.alarm(int(timeout_seconds))

            try:
                result = func(*args, **kwargs)
            except TimeoutError as e:
                duration = time.time() - start_time
                _log_timeout(sample_id, duration, str(e))
                # Return sentinel value to allow pipeline to continue
                return None
            except Exception as e:
                # Log other exceptions as well if they occur during timeout window
                # but only if they are not TimeoutError (already handled)
                duration = time.time() - start_time
                _log_timeout(sample_id, duration, f"Unexpected error: {str(e)}")
                return None
            finally:
                # Cancel the alarm and restore the old handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

            return result
        return wrapper
    return decorator


def timeout_wrapper(
    func: Callable,
    timeout_seconds: float,
    sample_id: str
) -> Callable:
    """
    Wraps a function to enforce a timeout for a specific sample.

    This is an imperative alternative to the decorator approach, useful
    when the function cannot be decorated directly or when dynamic
    wrapping is required.

    Args:
        func: The callable to wrap.
        timeout_seconds: Maximum allowed execution time.
        sample_id: Identifier for the current sample (used in logging).

    Returns:
        A new callable that executes `func` with the timeout constraint.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = None

        def handler(signum, frame):
            raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds}s")

        old_handler = signal.signal(signal.SIGALRM, handler)
        signal.alarm(int(timeout_seconds))

        try:
            result = func(*args, **kwargs)
        except TimeoutError as e:
            duration = time.time() - start_time
            _log_timeout(sample_id, duration, str(e))
            return None
        except Exception as e:
            duration = time.time() - start_time
            _log_timeout(sample_id, duration, f"Unexpected error: {str(e)}")
            return None
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

        return result
    return wrapper
