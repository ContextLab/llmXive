"""
Timeout decorator to enforce per-task limits and handle graceful skips.
Enforces limits in minutes as per T008 specification.
"""
import signal
import time
import logging
from functools import wraps
from typing import Callable, Optional, Any
from utils.logger import log_timeout_error, get_memory_log_path

logger = logging.getLogger(__name__)

class TaskTimeoutError(Exception):
    """Exception raised when a task exceeds its time limit."""
    pass

def timeout_decorator(minutes: float):
    """
    Decorator to enforce a time limit on a function.
    
    Args:
        minutes: Time limit in minutes.
        
    Returns:
        Decorated function that raises TaskTimeoutError if time is exceeded.
    """
    seconds = int(minutes * 60)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Define the signal handler
            def timeout_handler(signum, frame):
                task_name = func.__name__
                log_timeout_error(task_name, seconds)
                raise TaskTimeoutError(f"Task '{task_name}' exceeded {minutes} minute limit ({seconds}s). Skipping.")

            # Set the signal handler and alarm
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                # Reset the alarm and restore the old handler
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        
        return wrapper
    return decorator