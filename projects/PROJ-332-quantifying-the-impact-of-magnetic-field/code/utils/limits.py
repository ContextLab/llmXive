"""
Resource limits and guards for timeout and memory constraints.
Implements FR-007: Internal timeout wrapper to abort execution if threshold exceeded.
"""
import os
import signal
import sys
import resource
from functools import wraps
from contextlib import contextmanager
from typing import Callable, Any, Optional
import threading

class TimeoutError(Exception):
    """Exception raised when a timeout occurs."""
    pass

class MemoryLimitError(Exception):
    """Exception raised when memory limit is exceeded."""
    pass

def timeout_guard(seconds: int):
    """
    Decorator to enforce a timeout on a function execution.
    
    If the function execution exceeds `seconds`, the Python process
    will be aborted via a signal handler raising TimeoutError.
    
    Args:
        seconds: Maximum execution time in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Set up signal handler for timeout
            def timeout_handler(signum, frame):
                # Log the timeout event before exiting if logger is available
                try:
                    from utils.logger import get_logger
                    logger = get_logger()
                    logger.error(f"Process timeout: {func.__name__} exceeded {seconds}s")
                except Exception:
                    pass
                # Raise the exception to be caught by the caller or let it crash the process
                raise TimeoutError(f"Function {func.__name__} exceeded timeout of {seconds} seconds")
            
            # Save old handler
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            
            try:
                signal.alarm(seconds)
                result = func(*args, **kwargs)
                return result
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        
        return wrapper
    return decorator

@contextmanager
def timeout_context(seconds: int):
    """
    Context manager for timeout enforcement.
    
    Args:
        seconds: Maximum execution time in seconds
    """
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation exceeded timeout of {seconds} seconds")
    
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    try:
        signal.alarm(seconds)
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def get_memory_usage_mb() -> float:
    """
    Get current memory usage in megabytes.
    
    Returns:
        Current memory usage in MB
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in kilobytes on Linux
    return usage.ru_maxrss / 1024.0

def check_memory_usage(limit_mb: float) -> bool:
    """
    Check if current memory usage is within limits.
    
    Args:
        limit_mb: Maximum allowed memory in MB
        
    Returns:
        True if within limits, False otherwise
    """
    current = get_memory_usage_mb()
    return current < limit_mb

def memory_guard(limit_mb: float):
    """
    Decorator to enforce memory limits on function execution.
    
    Args:
        limit_mb: Maximum allowed memory in MB
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not check_memory_usage(limit_mb):
                raise MemoryLimitError(
                    f"Memory limit exceeded: {get_memory_usage_mb():.2f}MB > {limit_mb}MB"
                )
            
            result = func(*args, **kwargs)
            
            if not check_memory_usage(limit_mb):
                raise MemoryLimitError(
                    f"Memory limit exceeded after execution: {get_memory_usage_mb():.2f}MB > {limit_mb}MB"
                )
            
            return result
        
        return wrapper
    return decorator
