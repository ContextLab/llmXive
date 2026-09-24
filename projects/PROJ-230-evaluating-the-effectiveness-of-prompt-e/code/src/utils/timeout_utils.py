"""
Timeout utilities for enforcing API and test execution timeouts.

This module provides mechanisms to enforce strict time limits on:
- API calls (120s default) as required by FR-002
- Test executions (10s default) as required by FR-003

It uses threading and signal-based timeouts to ensure execution stops
within the specified limits, raising a custom TimeoutError exception.
"""
import signal
import time
import threading
import sys
from functools import wraps
from typing import Callable, Any, Optional, Type


class TimeoutError(Exception):
    """Custom exception raised when a timeout occurs."""
    pass


class TimeoutHandler:
    """
    A context manager and decorator for enforcing timeouts.
    
    Uses threading for cross-platform compatibility (works on Windows),
    falling back to signal-based timeouts on Unix-like systems when possible.
    """
    
    def __init__(self, timeout_seconds: float, error_message: Optional[str] = None):
        """
        Initialize the timeout handler.
        
        Args:
            timeout_seconds: Maximum allowed execution time in seconds.
            error_message: Optional custom error message. Defaults to generic message.
        """
        self.timeout_seconds = timeout_seconds
        self.error_message = error_message or f"Operation timed out after {timeout_seconds} seconds"
        self._thread: Optional[threading.Thread] = None
        self._exception: Optional[Exception] = None
        self._result: Any = None
        self._completed = threading.Event()
    
    def _run_function(self, func: Callable, args: tuple, kwargs: dict) -> None:
        """Internal method to run the target function in a separate thread."""
        try:
            self._result = func(*args, **kwargs)
        except Exception as e:
            self._exception = e
        finally:
            self._completed.set()
    
    def __enter__(self) -> 'TimeoutHandler':
        """Enter the context manager; starts the timeout timer."""
        self._thread = threading.Thread(target=self._run_function, args=(), kwargs={})
        self._thread.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """
        Exit the context manager; waits for completion or raises TimeoutError.
        
        Returns:
            False to propagate any exceptions that occurred.
        """
        self._completed.wait(timeout=self.timeout_seconds)
        
        if not self._completed.is_set():
            raise TimeoutError(self.error_message)
        
        if self._exception is not None:
            raise self._exception
        
        return False
    
    def __call__(self, func: Callable) -> Callable:
        """
        Decorator to apply timeout to a function.
        
        Args:
            func: The function to wrap.
            
        Returns:
            A wrapped function that enforces the timeout.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                # This will raise TimeoutError if the timeout expires
                # or re-raise any exception from the function
                pass
            # If we get here, the function completed within the timeout
            # We need to actually run the function inside the timeout context
            return self._run_with_timeout(func, args, kwargs)
        
        return wrapper
    
    def _run_with_timeout(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """Run the function with timeout enforcement."""
        self._thread = threading.Thread(target=self._run_function, args=(func, args, kwargs))
        self._thread.daemon = True
        self._thread.start()
        
        if not self._completed.wait(timeout=self.timeout_seconds):
            raise TimeoutError(self.error_message)
        
        if self._exception is not None:
            raise self._exception
        
        return self._result


def enforce_api_timeout(func: Callable) -> Callable:
    """
    Decorator to enforce a 120-second timeout on API calls.
    
    Args:
        func: The API call function to wrap.
        
    Returns:
        A wrapped function that enforces the 120s timeout.
    """
    timeout_handler = TimeoutHandler(120.0, "API call timed out after 120 seconds")
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        return timeout_handler._run_with_timeout(func, args, kwargs)
    
    return wrapper


def enforce_test_timeout(func: Callable) -> Callable:
    """
    Decorator to enforce a 10-second timeout on test executions.
    
    Args:
        func: The test function to wrap.
        
    Returns:
        A wrapped function that enforces the 10s timeout.
    """
    timeout_handler = TimeoutHandler(10.0, "Test execution timed out after 10 seconds")
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        return timeout_handler._run_with_timeout(func, args, kwargs)
    
    return wrapper


def run_with_api_timeout(func: Callable, *args, **kwargs) -> Any:
    """
    Execute a function with a 120-second timeout.
    
    This is a helper function for one-off API calls without using decorators.
    
    Args:
        func: The function to execute.
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.
        
    Returns:
        The result of the function if it completes within the timeout.
        
    Raises:
        TimeoutError: If the function exceeds 120 seconds.
        Exception: Any exception raised by the function.
    """
    handler = TimeoutHandler(120.0, "API operation timed out after 120 seconds")
    return handler._run_with_timeout(func, args, kwargs)


def run_with_test_timeout(func: Callable, *args, **kwargs) -> Any:
    """
    Execute a function with a 10-second timeout.
    
    This is a helper function for one-off test executions without using decorators.
    
    Args:
        func: The function to execute.
        *args: Positional arguments to pass to the function.
        **kwargs: Keyword arguments to pass to the function.
        
    Returns:
        The result of the function if it completes within the timeout.
        
    Raises:
        TimeoutError: If the function exceeds 10 seconds.
        Exception: Any exception raised by the function.
    """
    handler = TimeoutHandler(10.0, "Test operation timed out after 10 seconds")
    return handler._run_with_timeout(func, args, kwargs)


# Signal-based timeout for Unix-like systems (more efficient than threading)
if sys.platform != 'win32':
    def _signal_timeout_handler(signum, frame):
        """Signal handler for timeout events."""
        raise TimeoutError("Operation timed out")
    
    def signal_based_timeout(func: Callable, timeout_seconds: float, *args, **kwargs) -> Any:
        """
        Execute a function with a signal-based timeout (Unix only).
        
        This is more efficient than threading for CPU-bound operations.
        
        Args:
            func: The function to execute.
            timeout_seconds: Maximum allowed execution time.
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.
            
        Returns:
            The result of the function if it completes within the timeout.
            
        Raises:
            TimeoutError: If the function exceeds the timeout.
            Exception: Any exception raised by the function.
        """
        # Save the old signal handler
        old_handler = signal.signal(signal.SIGALRM, _signal_timeout_handler)
        
        try:
            # Set the alarm
            signal.alarm(int(timeout_seconds))
            result = func(*args, **kwargs)
            return result
        finally:
            # Cancel the alarm and restore the old handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

else:
    # Windows doesn't support SIGALRM, so we use the threading-based approach
    def signal_based_timeout(func: Callable, timeout_seconds: float, *args, **kwargs) -> Any:
        """
        Fallback for Windows: use threading-based timeout.
        """
        handler = TimeoutHandler(timeout_seconds, f"Operation timed out after {timeout_seconds} seconds")
        return handler._run_with_timeout(func, args, kwargs)