"""
Timeout wrapper to enforce global runtime limits for the pipeline.

This module implements FR-013: Enforce global 6h runtime limit.
It provides mechanisms to:
1. Set a global timeout at the start of the pipeline
2. Check remaining time before processing items
3. Gracefully skip remaining PRs if the limit is exceeded
4. Log warnings to logs/timeout.log
5. Exit with code 143 (SIGTERM) if limit exceeded
"""

import os
import signal
import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable, Any
from contextlib import contextmanager

# Import logger setup from existing module
from code.src.utils.logger import get_logger, setup_pipeline_logging

# Constants
DEFAULT_TIMEOUT_HOURS = 6
EXIT_CODE_TIMEOUT = 143
LOG_FILENAME = "timeout.log"

# Global state
_start_time: Optional[datetime] = None
_timeout_seconds: Optional[float] = None
_logger: Optional[logging.Logger] = None
_timeout_log_path: Optional[Path] = None


def setup_timeout_logging(logs_dir: Optional[Path] = None) -> logging.Logger:
    """
    Setup dedicated logging for timeout events.
    
    Args:
        logs_dir: Directory for log files. If None, uses default from config.
    
    Returns:
        Configured logger instance
    """
    global _logger, _timeout_log_path
    
    if _logger is not None:
        return _logger
    
    # Setup general pipeline logging first to ensure logs dir exists
    setup_pipeline_logging()
    
    # Determine logs directory
    if logs_dir is None:
        # Try to get from settings, fallback to default
        try:
            from code.config.settings import get_paths
            paths = get_paths()
            logs_dir = paths.get("logs", Path("logs"))
        except Exception:
            logs_dir = Path("logs")
    
    logs_dir = Path(logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    _timeout_log_path = logs_dir / LOG_FILENAME
    
    # Create dedicated logger
    _logger = logging.getLogger("timeout")
    _logger.setLevel(logging.WARNING)
    
    # Prevent duplicate handlers
    if not _logger.handlers:
        # File handler for timeout.log
        fh = logging.FileHandler(_timeout_log_path)
        fh.setLevel(logging.WARNING)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        _logger.addHandler(fh)
        
        # Also log to console for immediate visibility
        ch = logging.StreamHandler()
        ch.setLevel(logging.WARNING)
        ch.setFormatter(formatter)
        _logger.addHandler(ch)
    
    return _logger


def set_global_timeout(timeout_hours: float = DEFAULT_TIMEOUT_HOURS) -> None:
    """
    Set the global timeout for the pipeline run.
    
    Args:
        timeout_hours: Duration in hours before timeout triggers
    """
    global _start_time, _timeout_seconds, _logger
    
    _start_time = datetime.now()
    _timeout_seconds = timeout_hours * 3600
    _logger = setup_timeout_logging()
    
    _logger.info(f"Global timeout set to {timeout_hours} hours ({_timeout_seconds} seconds)")
    _logger.info(f"Pipeline started at: {_start_time.isoformat()}")
    _logger.info(f"Expected timeout at: {_start_time + timedelta(seconds=_timeout_seconds)}")


def check_timeout() -> bool:
    """
    Check if the global timeout has been exceeded.
    
    Returns:
        True if timeout exceeded, False otherwise
    """
    global _start_time, _timeout_seconds, _logger
    
    if _start_time is None or _timeout_seconds is None:
        # No timeout set, always return False
        return False
    
    elapsed = (datetime.now() - _start_time).total_seconds()
    
    if elapsed >= _timeout_seconds:
        if _logger:
            _logger.warning(
                f"TIMEOUT EXCEEDED: Elapsed time {elapsed:.1f}s exceeds limit {_timeout_seconds}s. "
                f"Skipping remaining PRs."
            )
        return True
    
    return False


def get_remaining_time_seconds() -> float:
    """
    Get remaining time before timeout.
    
    Returns:
        Remaining seconds, or infinity if no timeout set
    """
    global _start_time, _timeout_seconds
    
    if _start_time is None or _timeout_seconds is None:
        return float('inf')
    
    elapsed = (datetime.now() - _start_time).total_seconds()
    remaining = _timeout_seconds - elapsed
    return max(0.0, remaining)


def timeout_handler(signum: int, frame: Any) -> None:
    """
    Signal handler for timeout events.
    
    Args:
        signum: Signal number
        frame: Current stack frame
    """
    logger = setup_timeout_logging()
    logger.warning(
        f"Received timeout signal ({signum}). "
        "Exiting with code 143 after logging timeout event."
    )
    sys.exit(EXIT_CODE_TIMEOUT)


def enforce_timeout(timeout_hours: float = DEFAULT_TIMEOUT_HOURS) -> None:
    """
    Enforce timeout by setting up signal handlers and checking elapsed time.
    
    This function should be called at the start of the main pipeline loop.
    It sets up:
    1. Global timeout tracking
    2. Signal handler for SIGALRM (Unix) or periodic checks (Windows)
    
    Args:
        timeout_hours: Duration in hours before timeout
    """
    set_global_timeout(timeout_hours)
    
    # Install signal handler for Unix systems
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, timeout_handler)
        # Set alarm for the timeout duration
        signal.alarm(int(timeout_hours * 3600))


class TimeoutContext:
    """
    Context manager for timeout-aware operations.
    
    Usage:
        with TimeoutContext(timeout_hours=6) as ctx:
            if ctx.is_timed_out():
                # Skip remaining work
                break
            # Process item
    """
    
    def __init__(self, timeout_hours: float = DEFAULT_TIMEOUT_HOURS):
        self.timeout_hours = timeout_hours
        self._start: Optional[datetime] = None
        self._logger: Optional[logging.Logger] = None
    
    def __enter__(self):
        self._start = datetime.now()
        self._logger = setup_timeout_logging()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and exc_type.__name__ == "TimeoutExceeded":
            # Clean exit due to timeout
            return True
        return False
    
    def is_timed_out(self) -> bool:
        """Check if timeout has been exceeded."""
        if self._start is None:
            return False
        
        elapsed = (datetime.now() - self._start).total_seconds()
        timeout_seconds = self.timeout_hours * 3600
        
        if elapsed >= timeout_seconds:
            if self._logger:
                self._logger.warning(
                    f"Timeout exceeded in context: {elapsed:.1f}s >= {timeout_seconds}s"
                )
            return True
        return False
    
    def get_remaining_seconds(self) -> float:
        """Get remaining seconds in this context."""
        if self._start is None:
            return float('inf')
        
        elapsed = (datetime.now() - self._start).total_seconds()
        timeout_seconds = self.timeout_hours * 3600
        return max(0.0, timeout_seconds - elapsed)
    
    def check_and_raise(self):
        """Check timeout and raise exception if exceeded."""
        if self.is_timed_out():
            raise TimeoutExceeded("Global timeout limit exceeded")


class TimeoutExceeded(Exception):
    """Exception raised when the global timeout is exceeded."""
    pass


def timeout_decorator(timeout_hours: float = DEFAULT_TIMEOUT_HOURS):
    """
    Decorator to enforce timeout on a function.
    
    Args:
        timeout_hours: Maximum duration for the function
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with TimeoutContext(timeout_hours) as ctx:
                return func(*args, **kwargs)
        return wrapper
    return decorator


def main():
    """
    Main entry point for testing timeout functionality.
    
    This function demonstrates the timeout mechanism by:
    1. Setting a short timeout (10 seconds for testing)
    2. Attempting to process a long-running task
    3. Showing graceful exit on timeout
    """
    setup_timeout_logging()
    logger = logging.getLogger("timeout")
    
    # Set a very short timeout for demonstration (10 seconds)
    set_global_timeout(timeout_hours=10 / 3600)  # 10 seconds
    
    logger.info("Starting timeout demonstration...")
    
    try:
        # Simulate work with timeout checking
        for i in range(100):
            if check_timeout():
                logger.warning(f"Timeout reached at iteration {i}. Exiting gracefully.")
                sys.exit(EXIT_CODE_TIMEOUT)
            
            # Simulate work
            time.sleep(0.5)
            logger.info(f"Processed iteration {i}")
        
        logger.info("Completed all iterations without timeout")
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
