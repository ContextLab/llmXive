"""
Error handling utilities for TLE (Timeout) and OOM (Out of Memory) detection and logging.

This module provides decorators and helper functions to robustly handle common
failure modes in LLM inference and data processing pipelines, specifically:
- Timeout errors (TLE)
- Out of Memory errors (OOM)
- General execution failures

It integrates with the project's logging configuration and provides structured
error reporting for downstream analysis.
"""
import logging
import signal
import sys
import time
from functools import wraps
from typing import Callable, Any, Optional, Tuple, Type
from contextlib import contextmanager

# Configure logging to use the project standard
logger = logging.getLogger(__name__)

class ExecutionTimeoutError(Exception):
    """Raised when a function exceeds its time limit."""
    def __init__(self, message: str, duration: float):
        super().__init__(message)
        self.duration = duration
        self.error_code = "TLE"

class OutOfMemoryError(Exception):
    """Raised when a process runs out of memory."""
    def __init__(self, message: str = "Out of memory"):
        super().__init__(message)
        self.error_code = "OOM"

class ExecutionError(Exception):
    """Generic execution failure wrapper."""
    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error
        self.error_code = "EXEC_FAIL"

def log_error(error_type: str, message: str, details: Optional[dict] = None):
    """
    Standardized error logging function.
    
    Args:
        error_type: Type of error (TLE, OOM, EXEC_FAIL)
        message: Human-readable description
        details: Optional dictionary of additional context
    """
    log_msg = f"[{error_type}] {message}"
    if details:
        log_msg += f" | Details: {details}"
    
    logger.error(log_msg)
    
    # Also print to stderr for immediate visibility during scripts
    print(f"⚠️ ERROR [{error_type}]: {message}", file=sys.stderr)
    if details:
        print(f"   Context: {details}", file=sys.stderr)

def handle_timeout(signum, frame):
    """Signal handler for timeout events."""
    raise ExecutionTimeoutError("Function execution timed out", duration=0)

@contextmanager
def timeout_context(seconds: int):
    """
    Context manager to enforce a timeout on a block of code.
    
    Args:
        seconds: Maximum execution time in seconds
        
    Yields:
        None
        
    Raises:
        ExecutionTimeoutError: If the timeout is exceeded
    """
    if not hasattr(signal, 'SIGALRM'):
        # SIGALRM not available on Windows, skip timeout enforcement
        yield
        return
        
    old_handler = signal.signal(signal.SIGALRM, handle_timeout)
    try:
        signal.alarm(seconds)
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

def with_timeout(seconds: int, fallback_value: Any = None):
    """
    Decorator to add timeout protection to a function.
    
    Args:
        seconds: Maximum execution time in seconds
        fallback_value: Value to return if timeout occurs
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Tuple[Any, Optional[dict]]:
            try:
                if hasattr(signal, 'SIGALRM'):
                    with timeout_context(seconds):
                        result = func(*args, **kwargs)
                        return result, None
                else:
                    # No signal support, run without timeout
                    result = func(*args, **kwargs)
                    return result, None
            except ExecutionTimeoutError as e:
                log_error(
                    "TLE",
                    f"Function {func.__name__} timed out after {e.duration}s",
                    {"function": func.__name__, "timeout_seconds": seconds}
                )
                return fallback_value, {"error": "TLE", "function": func.__name__}
            except Exception as e:
                # Re-raise non-timeout exceptions
                raise
        return wrapper
    return decorator

def detect_oom_exception(e: Exception) -> bool:
    """
    Detect if an exception indicates an Out of Memory condition.
    
    Checks for common OOM patterns in PyTorch, TensorFlow, and system messages.
    
    Args:
        e: The exception to check
        
    Returns:
        True if the exception appears to be an OOM error
    """
    error_msg = str(e).lower()
    
    # Common OOM patterns
    oom_patterns = [
        "out of memory",
        "oom",
        "cuda out of memory",
        "allocating",
        "cannot allocate memory",
        "memory exhausted",
        "malloc",
        "virtual memory exhausted"
    ]
    
    for pattern in oom_patterns:
        if pattern in error_msg:
            return True
            
    return False

def handle_execution(func: Callable, max_retries: int = 1, timeout_seconds: Optional[int] = None):
    """
    Decorator to handle execution errors with retry logic and OOM detection.
    
    Args:
        func: Function to decorate
        max_retries: Number of retry attempts
        timeout_seconds: Optional timeout in seconds
        
    Returns:
        Decorated function with error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                if timeout_seconds and hasattr(signal, 'SIGALRM'):
                    with timeout_context(timeout_seconds):
                        result = func(*args, **kwargs)
                        return result, None
                else:
                    result = func(*args, **kwargs)
                    return result, None
                        
            except ExecutionTimeoutError as e:
                last_error = e
                log_error(
                    "TLE",
                    f"Function {func.__name__} timed out (attempt {attempt + 1}/{max_retries + 1})",
                    {"attempt": attempt + 1, "max_retries": max_retries, "timeout": timeout_seconds}
                )
                if attempt == max_retries:
                    return None, {"error": "TLE", "function": func.__name__, "attempts": attempt + 1}
                    
            except Exception as e:
                if detect_oom_exception(e):
                    last_error = OutOfMemoryError(str(e))
                    log_error(
                        "OOM",
                        f"Function {func.__name__} encountered OOM (attempt {attempt + 1}/{max_retries + 1})",
                        {"attempt": attempt + 1, "max_retries": max_retries, "error": str(e)}
                    )
                    if attempt == max_retries:
                        return None, {"error": "OOM", "function": func.__name__, "attempts": attempt + 1}
                else:
                    last_error = e
                    log_error(
                        "EXEC_FAIL",
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1})",
                        {"attempt": attempt + 1, "max_retries": max_retries, "error": str(e)}
                    )
                    if attempt == max_retries:
                        return None, {"error": "EXEC_FAIL", "function": func.__name__, "attempts": attempt + 1, "original": str(e)}
            
            # Small delay before retry
            if attempt < max_retries:
                time.sleep(1.0 * (attempt + 1))  # Exponential backoff
        
        return None, {"error": "MAX_RETRIES", "function": func.__name__, "attempts": max_retries + 1}
        
    return wrapper

def safe_execute(func: Callable, *args, **kwargs) -> Tuple[Any, Optional[dict]]:
    """
    Safely execute a function with comprehensive error handling.
    
    This is the primary entry point for executing potentially unstable code.
    It wraps the function with timeout and OOM detection, returning both
    the result (or None) and an error status dictionary.
    
    Args:
        func: Function to execute
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Tuple of (result, error_info) where error_info is None on success
    """
    try:
        result = func(*args, **kwargs)
        return result, None
    except ExecutionTimeoutError as e:
        log_error("TLE", f"Execution failed: {e}", {"duration": e.duration})
        return None, {"error": "TLE", "duration": e.duration}
    except Exception as e:
        if detect_oom_exception(e):
            log_error("OOM", f"Execution failed: {e}")
            return None, {"error": "OOM", "message": str(e)}
        else:
            log_error("EXEC_FAIL", f"Execution failed: {e}", {"exception_type": type(e).__name__})
            return None, {"error": "EXEC_FAIL", "message": str(e), "type": type(e).__name__}