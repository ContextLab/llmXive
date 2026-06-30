"""
Timeout enforcement utilities for benchmark tasks.
Implements FR-006 (Task Execution) and FR-013 (Resource Constraints).
"""
import signal
import threading
from functools import wraps
from typing import Callable, Any, Optional, Union

class TimeoutError(Exception):
    """Custom timeout error for task execution limits."""
    pass


def _timeout_handler(signum, frame):
    """Signal handler for Unix-based timeout enforcement."""
    raise TimeoutError("Task execution exceeded the allowed timeout limit.")


def enforce_timeout(
    func: Callable,
    timeout_seconds: int = 300,
    use_signals: Optional[bool] = None
) -> Callable:
    """
    Decorator to enforce a maximum execution time for a function.

    If the function runs longer than `timeout_seconds`, a TimeoutError is raised.

    On Unix-like systems (Linux/macOS), uses `signal.SIGALRM` for precise enforcement.
    On Windows or in threaded environments where signals are limited, falls back to
    a daemon thread watchdog approach.

    Args:
        func: The function to wrap.
        timeout_seconds: Maximum allowed execution time in seconds (default 300).
        use_signals: Force signal-based timeout (Unix only). If None, auto-detects.

    Returns:
        The wrapped function.

    Raises:
        TimeoutError: If the function execution exceeds `timeout_seconds`.
    """
    # Determine if we can use signal-based timeout
    # Signal-based timeout only works in the main thread on Unix
    can_use_signals = (
        use_signals is True or
        (use_signals is None and hasattr(signal, 'SIGALRM') and threading.current_thread() is threading.main_thread())
    )

    if can_use_signals:
        def signal_decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                # Set the signal handler
                old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
                try:
                    # Set the alarm
                    signal.alarm(timeout_seconds)
                    try:
                        return f(*args, **kwargs)
                    finally:
                        # Cancel the alarm
                        signal.alarm(0)
                finally:
                    # Restore the old handler
                    signal.signal(signal.SIGALRM, old_handler)
            return wrapper
        return signal_decorator(func)
    else:
        # Fallback to threading watchdog for Windows or non-main threads
        def threading_decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                result_container = {"value": None, "error": None, "done": threading.Event()}

                def target():
                    try:
                        result_container["value"] = f(*args, **kwargs)
                    except Exception as e:
                        result_container["error"] = e
                    finally:
                        result_container["done"].set()

                thread = threading.Thread(target=target, daemon=True)
                thread.start()
                
                if not result_container["done"].wait(timeout=timeout_seconds):
                    raise TimeoutError(
                        f"Task execution exceeded the allowed timeout limit of {timeout_seconds} seconds."
                    )
                
                if result_container["error"]:
                    raise result_container["error"]
                
                return result_container["value"]
            return wrapper
        return threading_decorator(func)

# Convenience function for one-off execution without decoration
def run_with_timeout(
    func: Callable,
    timeout_seconds: int = 300,
    *args,
    **kwargs
) -> Any:
    """
    Execute a function with a timeout constraint.

    Args:
        func: The function to execute.
        timeout_seconds: Maximum allowed execution time.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.

    Returns:
        The return value of the function.

    Raises:
        TimeoutError: If the function execution exceeds `timeout_seconds`.
    """
    # Apply the decorator temporarily
    wrapped = enforce_timeout(func, timeout_seconds)
    return wrapped(*args, **kwargs)
