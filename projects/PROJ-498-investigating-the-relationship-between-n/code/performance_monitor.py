import time
import sys
import os
import resource
from pathlib import Path
from typing import Callable, Any, Optional

def ensure_logs_dir() -> None:
    """Ensure the logs directory exists."""
    logs_dir = Path("logs")
    if not logs_dir.exists():
        logs_dir.mkdir(parents=True, exist_ok=True)

def get_rss_mb() -> float:
    """
    Get the current Resident Set Size (RSS) memory usage in megabytes.
    
    Returns:
        float: Current RSS in MB.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # maxrss is in kilobytes on Linux/macOS, but units vary by OS.
    # On Linux, it's KB. On macOS, it's KB.
    # We assume KB for standard POSIX behavior in this context.
    return usage.ru_maxrss / 1024.0

def enforce_time_limit(
    func: Callable[..., Any],
    time_limit_seconds: float,
    *args: Any,
    **kwargs: Any
) -> Any:
    """
    Execute a function with a hard time limit.
    
    If the function execution exceeds `time_limit_seconds`, a TimeoutError is raised.
    This uses `signal` on Unix-like systems. On Windows, this falls back to a
    soft check or raises NotImplementedError if hard limits are strictly required
    but not available via signal.alarm.
    
    Args:
        func: The function to execute.
        time_limit_seconds: Maximum allowed execution time in seconds.
        *args: Arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.
        
    Returns:
        The return value of the function if it completes in time.
        
    Raises:
        TimeoutError: If the function execution exceeds the time limit.
        NotImplementedError: If hard timeout enforcement is not supported on this OS.
    """
    if sys.platform == "win32":
        # Windows does not support signal.alarm for hard timeouts in the same way.
        # We perform a soft check by timing the execution.
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        if elapsed > time_limit_seconds:
            raise TimeoutError(
                f"Function {func.__name__} took {elapsed:.2f}s, "
                f"exceeding limit of {time_limit_seconds}s."
            )
        return result

    # Unix-like systems (Linux, macOS)
    def timeout_handler(signum, frame):
        raise TimeoutError(
            f"Function {func.__name__} exceeded time limit of {time_limit_seconds}s."
        )

    # Set the signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    
    # Set the alarm
    try:
        signal.alarm(int(time_limit_seconds))
        result = func(*args, **kwargs)
        return result
    finally:
        # Cancel the alarm and restore the old handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def main() -> None:
    """
    CLI entry point for performance monitoring utilities.
    Currently a placeholder for potential future CLI commands.
    """
    print("Performance Monitor Utility")
    print(f"Current RSS: {get_rss_mb():.2f} MB")

if __name__ == "__main__":
    main()
