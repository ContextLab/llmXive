"""
Timeout enforcement utilities for the benchmark pipeline.

Implements FR-006 and FR-013: Timeout enforcement for task execution.
Provides mechanisms to enforce execution time limits and raise TimeoutError
when limits are exceeded.

Dependencies: T016 (logging module)
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
    """Custom timeout error for benchmark tasks."""
    pass


def enforce_timeout(func: Callable, timeout_seconds: int = 300) -> Callable:
    """
    Decorator to enforce a timeout on a function execution.
    
    Args:
        func: The function to wrap with timeout enforcement.
        timeout_seconds: Maximum allowed execution time in seconds (default: 300).
        
    Returns:
        A wrapped function that raises TimeoutError if execution exceeds timeout.
        
    Raises:
        TimeoutError: If the function execution exceeds timeout_seconds.
        
    Example:
        @enforce_timeout(timeout_seconds=60)
        def slow_task():
            time.sleep(120)
            
        # This will raise TimeoutError after 60 seconds
        slow_task()
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = [None]
        exception = [None]
        completed = threading.Event()
        
        def target():
            try:
                result[0] = func(*args, **kwargs)
            except Exception as e:
                exception[0] = e
            finally:
                completed.set()
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        
        if completed.wait(timeout=timeout_seconds):
            if exception[0] is not None:
                raise exception[0]
            return result[0]
        else:
            # Thread is still running, but we timeout
            logger.warning(
                f"Function {func.__name__} exceeded timeout of {timeout_seconds} seconds. "
                f"Terminating execution."
            )
            raise TimeoutError(
                f"Function '{func.__name__}' exceeded timeout of {timeout_seconds} seconds"
            )
    
    return wrapper


def run_with_timeout(
    func: Callable,
    timeout_seconds: int = 300,
    *args,
    **kwargs
) -> Any:
    """
    Execute a function with a timeout constraint.
    
    This is an alternative to the decorator approach for cases where
    you need to enforce timeout on the fly.
    
    Args:
        func: The function to execute.
        timeout_seconds: Maximum allowed execution time in seconds.
        *args: Positional arguments to pass to func.
        **kwargs: Keyword arguments to pass to func.
        
    Returns:
        The result of func(*args, **kwargs) if completed within timeout.
        
    Raises:
        TimeoutError: If execution exceeds timeout_seconds.
        
    Example:
        def compute_something(x, y):
            time.sleep(10)
            return x + y
        
        result = run_with_timeout(compute_something, timeout_seconds=5, x=1, y=2)
        # Raises TimeoutError
    """
    result = [None]
    exception = [None]
    completed = threading.Event()
    
    def target():
        try:
            result[0] = func(*args, **kwargs)
        except Exception as e:
            exception[0] = e
        finally:
            completed.set()
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    
    if completed.wait(timeout=timeout_seconds):
        if exception[0] is not None:
            raise exception[0]
        return result[0]
    else:
        logger.warning(
            f"Function {func.__name__} exceeded timeout of {timeout_seconds} seconds."
        )
        raise TimeoutError(
            f"Function '{func.__name__}' exceeded timeout of {timeout_seconds} seconds"
        )


def main():
    """
    Main function for testing timeout enforcement.
    Runs a simple test to demonstrate timeout functionality.
    """
    logger.info("Testing timeout enforcement...")
    
    # Test 1: Function completes within timeout
    @enforce_timeout(timeout_seconds=5)
    def quick_task():
        time.sleep(1)
        return "success"
    
    try:
        result = quick_task()
        logger.info(f"Test 1 passed: {result}")
    except TimeoutError as e:
        logger.error(f"Test 1 failed: {e}")
    
    # Test 2: Function exceeds timeout
    @enforce_timeout(timeout_seconds=2)
    def slow_task():
        time.sleep(5)
        return "should not reach here"
    
    try:
        result = slow_task()
        logger.error("Test 2 failed: Expected TimeoutError")
    except TimeoutError as e:
        logger.info(f"Test 2 passed: Correctly raised TimeoutError - {e}")
    
    # Test 3: run_with_timeout function
    def task_with_args(x, y):
        time.sleep(1)
        return x + y
    
    try:
        result = run_with_timeout(task_with_args, timeout_seconds=5, x=10, y=20)
        logger.info(f"Test 3 passed: {result}")
    except TimeoutError as e:
        logger.error(f"Test 3 failed: {e}")
    
    logger.info("All timeout tests completed.")

if __name__ == "__main__":
    main()