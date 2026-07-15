import signal
import time
from functools import wraps
from typing import Callable, Any, Optional

class TimeoutError(Exception):
    """Exception raised when a function execution exceeds the allowed time."""
    pass

class TimeoutHandler:
    """
    Utility class for enforcing execution timeouts.
    
    Supports two modes:
    1. Unix signals (SIGALRM) for functions running in the main thread on Unix.
    2. Context manager for blocks of code (Unix only).
    
    Note: On Windows or non-main threads, signal-based timeouts are not available.
    In those cases, this implementation raises a RuntimeError if the platform
    does not support the required signal.
    """

    @staticmethod
    def _check_signal_support():
        """Check if the current platform supports SIGALRM."""
        if not hasattr(signal, 'SIGALRM'):
            raise RuntimeError(
                "Signal-based timeouts (SIGALRM) are not supported on this platform "
                "(e.g., Windows). Use a threading-based approach or run on Unix."
            )

    @staticmethod
    def _timeout_handler(signum, frame):
        """Signal handler that raises TimeoutError."""
        raise TimeoutError("Execution timed out.")

    @staticmethod
    def with_timeout(timeout_seconds: float, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with a strict timeout using SIGALRM.
        
        Args:
            timeout_seconds: Maximum time allowed for the function to run (seconds).
            func: The function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.
        
        Returns:
            The return value of the function.
        
        Raises:
            TimeoutError: If the function execution exceeds timeout_seconds.
            RuntimeError: If the platform does not support SIGALRM.
        """
        TimeoutHandler._check_signal_support()
        
        # Set the signal handler
        old_handler = signal.signal(signal.SIGALRM, TimeoutHandler._timeout_handler)
        
        try:
            # Schedule the alarm
            # Note: signal.alarm expects an integer. For sub-second precision,
            # we rely on the fact that the OS will fire the signal close to the time.
            # For precise sub-second timeouts, a threading approach is usually preferred,
            # but SIGALRM is the standard for synchronous blocking calls in Unix.
            signal.alarm(int(timeout_seconds) if timeout_seconds >= 1 else 1)
            
            if timeout_seconds < 1:
                # If sub-second is critical, we might need a fallback, 
                # but for API calls (120s) and tests (10s), integer seconds are sufficient.
                # If strict sub-second is needed, we would need a threading wrapper.
                pass

            result = func(*args, **kwargs)
            return result
        finally:
            # Cancel the alarm
            signal.alarm(0)
            # Restore the old handler
            signal.signal(signal.SIGALRM, old_handler)

    @staticmethod
    def timeout_context(timeout_seconds: float):
        """
        Returns a context manager that enforces a timeout on a block of code.
        
        Usage:
            with timeout_context(10):
                # code that must finish in 10 seconds
                do_something()
        
        Raises:
            TimeoutError: If the block exceeds the time limit.
        """
        return _TimeoutContextManager(timeout_seconds)

class _TimeoutContextManager:
    def __init__(self, timeout_seconds: float):
        self.timeout_seconds = timeout_seconds
        self.old_handler = None

    def __enter__(self):
        TimeoutHandler._check_signal_support()
        self.old_handler = signal.signal(signal.SIGALRM, TimeoutHandler._timeout_handler)
        signal.alarm(int(self.timeout_seconds) if self.timeout_seconds >= 1 else 1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        signal.alarm(0)
        signal.signal(signal.SIGALRM, self.old_handler)
        # Do not suppress exceptions
        return False

# Convenience wrappers for specific task requirements

def enforce_api_timeout(func: Callable) -> Callable:
    """
    Decorator to enforce a 120-second timeout on API calls.
    
    This is specifically designed for the 120s API timeout requirement in T009.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return TimeoutHandler.with_timeout(120, func, *args, **kwargs)
    return wrapper

def enforce_test_timeout(func: Callable) -> Callable:
    """
    Decorator to enforce a 10-second timeout on test executions.
    
    This is specifically designed for the 10s test timeout requirement in T009.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return TimeoutHandler.with_timeout(10, func, *args, **kwargs)
    return wrapper

def run_with_api_timeout(func: Callable, *args, **kwargs) -> Any:
    """
    Execute a function with a 120-second timeout.
    
    Direct helper for one-off API calls without decorators.
    """
    return TimeoutHandler.with_timeout(120, func, *args, **kwargs)

def run_with_test_timeout(func: Callable, *args, **kwargs) -> Any:
    """
    Execute a function with a 10-second timeout.
    
    Direct helper for one-off test runs without decorators.
    """
    return TimeoutHandler.with_timeout(10, func, *args, **kwargs)
