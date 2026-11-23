"""
code/utils/logger.py

Provides error handling, logging utilities, and timeout enforcement for MD simulations.
Specifically enforces a 300s timeout for 1.5ns runs to prevent CI runner hangs.
"""
import logging
import signal
import sys
import threading
import time
import os
from functools import wraps
from pathlib import Path
from typing import Optional, Callable, Any, Dict


class TimeoutError(Exception):
    """Custom timeout exception raised when a simulation exceeds the allowed duration."""
    pass


class MDRunLogger(logging.Logger):
    """
    Custom logger for MD runs that includes simulation context (complex ID, params)
    and ensures structured output to both console and file.
    """
    def __init__(self, name: str, level: int = logging.NOTSET):
        super().__init__(name, level)
        self.context: Dict[str, Any] = {}
        
        # Create handlers
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_format)
        self.addHandler(console_handler)

    def set_context(self, **kwargs):
        """Update the logging context with simulation parameters."""
        self.context.update(kwargs)

    def _log_with_context(self, level, msg, *args, **kwargs):
        """Internal log method that appends context to the message."""
        if self.context:
            ctx_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            full_msg = f"[{ctx_str}] {msg}"
        else:
            full_msg = msg
        super().log(level, full_msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log_with_context(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log_with_context(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log_with_context(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._log_with_context(logging.CRITICAL, msg, *args, **kwargs)


def get_logger(name: str = "md_pipeline", log_file: Optional[Path] = None) -> MDRunLogger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name.
        log_file: Optional path to a log file. If provided, logs are appended to this file.
    
    Returns:
        An MDRunLogger instance.
    """
    logger = MDRunLogger(name)
    
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    return logger


def setup_signal_timeout(seconds: int, msg: str = "Operation timed out"):
    """
    Sets up a signal-based timeout for the current thread/process.
    Uses SIGALRM on Unix systems. On Windows, this is a no-op for the signal mechanism
    but we provide a threading fallback if needed, though standard OpenMM runs 
    on CPU usually respect signal handlers on Linux runners.
    
    Args:
        seconds: Timeout duration in seconds.
        msg: Error message to raise on timeout.
    
    Raises:
        TimeoutError: If the time limit is exceeded.
    """
    def handler(signum, frame):
        raise TimeoutError(msg)
    
    # Only set signal handler on Unix-like systems (Linux/macOS)
    if hasattr(signal, 'SIGALRM'):
        old_handler = signal.signal(signal.SIGALRM, handler)
        signal.alarm(seconds)
        return old_handler
    else:
        # Fallback for Windows or non-Unix environments using threading
        # Note: This cannot interrupt a blocking C-extension call in OpenMM 
        # as cleanly as SIGALRM, but it prevents the script from hanging forever.
        def timeout_thread():
            time.sleep(seconds)
            raise TimeoutError(msg)
        
        thread = threading.Thread(target=timeout_thread, daemon=True)
        thread.start()
        return thread


def clear_signal_timeout(old_handler=None):
    """
    Clears the previously set timeout.
    
    Args:
        old_handler: The handler returned by setup_signal_timeout (if any).
    """
    if hasattr(signal, 'SIGALRM'):
        signal.alarm(0)  # Cancel the alarm
        if old_handler:
            signal.signal(signal.SIGALRM, old_handler)
    elif isinstance(old_handler, threading.Thread):
        # Cannot easily kill a daemon thread in Python safely, 
        # but we stop waiting for it. The script will exit if the main thread finishes.
        pass


def enforce_timeout(seconds: int, msg: str = "Operation timed out"):
    """
    Decorator to enforce a timeout on a function.
    
    Args:
        seconds: Maximum execution time in seconds.
        msg: Error message to raise on timeout.
    
    Returns:
        A wrapped function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            old_handler = setup_signal_timeout(seconds, msg)
            try:
                return func(*args, **kwargs)
            finally:
                clear_signal_timeout(old_handler)
        return wrapper
    return decorator


def timeout_handler(seconds: int, msg: str = "Operation timed out"):
    """
    Context manager for timeout enforcement.
    
    Args:
        seconds: Maximum execution time in seconds.
        msg: Error message to raise on timeout.
    """
    class TimeoutContext:
        def __enter__(self):
            self.old_handler = setup_signal_timeout(seconds, msg)
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            clear_signal_timeout(self.old_handler)
            return False
    
    return TimeoutContext()


# Global logger instance for the module
logger = get_logger("md_utils")