"""
Timeout decorator for long-running processes.
Raises TimeoutError if the function execution exceeds the specified limit.
"""
import signal
from functools import wraps
from typing import Callable, Any
import os
import time

class TimeoutError(Exception):
    """Custom timeout error exception."""
    pass

class TimeoutException(Exception):
    """Alias for compatibility, though TimeoutError is preferred."""
    pass


def timeout(seconds: int):
    """
    Decorator to enforce a time limit on a function.
    
    Args:
        seconds: Maximum execution time in seconds.
        
    Returns:
        Decorator function.
        
    Raises:
        TimeoutError: If the function execution exceeds the time limit.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Define the signal handler
            def handler(signum, frame):
                raise TimeoutError(f"Function '{func.__name__}' timed out after {seconds} seconds")

            # Set the signal handler and a timeout alarm
            # Note: signal.SIGALRM is only available on Unix-based systems
            if hasattr(signal, 'SIGALRM'):
                old_handler = signal.signal(signal.SIGALRM, handler)
                signal.alarm(seconds)
                
                try:
                    result = func(*args, **kwargs)
                finally:
                    # Cancel the alarm and restore the old handler
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
            else:
                # Fallback for Windows or systems without SIGALRM
                # Uses a threading approach or simply runs without timeout enforcement
                # For this pipeline, we assume a Unix-like environment (Linux runner)
                # If running on Windows, we could raise a warning or skip timeout
                import warnings
                warnings.warn("Timeout decorator requires Unix signal.SIGALRM. Running without timeout enforcement.")
                result = func(*args, **kwargs)
            
            return result
        return wrapper
    return decorator
