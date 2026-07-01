import signal
import threading
import time
from functools import wraps
from typing import Callable, Any, Optional, Union
import logging
from src.utils.logging import get_logger

logger = get_logger(__name__)

class TimeoutError(Exception):
    """Custom timeout exception."""
    pass

def enforce_timeout(func: Callable, timeout_seconds: int = 300) -> Any:
    """
    Execute a function with a timeout.
    
    Args:
        func: The function to execute
        timeout_seconds: Maximum execution time in seconds
        
    Returns:
        The result of the function
        
    Raises:
        TimeoutError: If the function exceeds the timeout
    """
    result = [None]
    exception = [None]
    
    def target():
        try:
            result[0] = func()
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout_seconds)
    
    if thread.is_alive():
        # Thread is still running, timeout occurred
        raise TimeoutError(f"Function {func.__name__} timed out after {timeout_seconds} seconds")
    
    if exception[0] is not None:
        raise exception[0]
    
    return result[0]

def run_with_timeout(func: Callable, timeout_seconds: int = 300):
    """
    Decorator to run a function with timeout.
    
    Args:
        func: The function to decorate
        timeout_seconds: Maximum execution time in seconds
        
    Returns:
        Wrapped function with timeout enforcement
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return enforce_timeout(lambda: func(*args, **kwargs), timeout_seconds)
    return wrapper

def main():
    """Test timeout functionality."""
    def fast_function():
        time.sleep(0.1)
        return "completed"
    
    def slow_function():
        time.sleep(5)
        return "should not reach here"
    
    # Test fast function
    try:
        result = enforce_timeout(fast_function, timeout_seconds=5)
        print(f"Fast function result: {result}")
    except TimeoutError as e:
        print(f"Fast function timeout: {e}")
    
    # Test slow function
    try:
        result = enforce_timeout(slow_function, timeout_seconds=1)
        print(f"Slow function result: {result}")
    except TimeoutError as e:
        print(f"Slow function timeout: {e}")

if __name__ == "__main__":
    main()
