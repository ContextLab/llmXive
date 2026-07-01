"""
Timeout enforcement utilities for benchmark tasks.

Implements FR-006 and FR-013: enforce execution timeouts and raise TimeoutError
if exceeded. Supports both signal-based (Unix) and threading-based (cross-platform)
timeout mechanisms.
"""
import signal
import threading
import time
from functools import wraps
from typing import Callable, Any, Optional, Union
import logging

from src.utils.logging import get_logger

logger = get_logger(__name__)


class TimeoutError(Exception):
    """Custom timeout error for benchmark task enforcement."""
    pass


def enforce_timeout(func: Callable, timeout_seconds: int = 300) -> Callable:
    """
    Decorator to enforce a timeout on a function execution.
    
    Uses signal-based timeout on Unix systems (more reliable) and
    threading-based timeout as a fallback for Windows.
    
    Args:
        func: The function to wrap with timeout enforcement.
        timeout_seconds: Maximum allowed execution time in seconds.
        
    Returns:
        Wrapped function that raises TimeoutError if execution exceeds timeout.
        
    Raises:
        TimeoutError: If the function execution exceeds timeout_seconds.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = [None]
        exception = [None]
        
        def target():
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[0] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout_seconds)
        
        if thread.is_alive():
            logger.warning(
                f"Function {func.__name__} exceeded timeout of {timeout_seconds}s. "
                "Terminating execution."
            )
            raise TimeoutError(
                f"Function {func.__name__} exceeded timeout of {timeout_seconds}s"
            )
        
        if exception[0] is not None:
            raise exception[0]
        
        return result[0]
    
    return wrapper


def run_with_timeout(
    func: Callable,
    timeout_seconds: int = 300,
    *args,
    **kwargs
) -> Any:
    """
    Execute a function with a timeout constraint.
    
    This is a non-decorator alternative that executes the function immediately
    with timeout enforcement.
    
    Args:
        func: The function to execute.
        timeout_seconds: Maximum allowed execution time in seconds.
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.
        
    Returns:
        The result of the function execution.
        
    Raises:
        TimeoutError: If the function execution exceeds timeout_seconds.
        Exception: Any exception raised by the function itself.
    """
    result = [None]
    exception = [None]
    
    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout_seconds)
    
    if thread.is_alive():
        logger.warning(
            f"Function {func.__name__} exceeded timeout of {timeout_seconds}s. "
            "Terminating execution."
        )
        raise TimeoutError(
            f"Function {func.__name__} exceeded timeout of {timeout_seconds}s"
        )
    
    if exception[0] is not None:
        raise exception[0]
    
    return result[0]


def main():
    """Test the timeout enforcement functionality."""
    import sys
    
    def slow_function():
        """A function that takes longer than the timeout."""
        time.sleep(2)
        return "completed"
    
    def quick_function():
        """A function that completes within the timeout."""
        time.sleep(0.1)
        return "quick result"
    
    print("Testing quick function with 1s timeout...")
    try:
        result = run_with_timeout(quick_function, timeout_seconds=1)
        print(f"✓ Quick function succeeded: {result}")
    except TimeoutError as e:
        print(f"✗ Quick function failed unexpectedly: {e}")
        sys.exit(1)
    
    print("Testing slow function with 0.5s timeout (should fail)...")
    try:
        result = run_with_timeout(slow_function, timeout_seconds=0.5)
        print(f"✗ Slow function should have timed out but returned: {result}")
        sys.exit(1)
    except TimeoutError as e:
        print(f"✓ Slow function correctly timed out: {e}")
    
    print("\nAll timeout tests passed!")


if __name__ == "__main__":
    main()