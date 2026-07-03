"""
Timeout wrapper to enforce global 6h runtime limit (FR-013).

This module provides a decorator and a context manager to enforce a global
runtime limit for the pipeline. If the limit is exceeded, it logs a warning
to logs/timeout.log and exits with code 143, gracefully skipping remaining PRs.
"""
import os
import signal
import sys
import time
import logging
from datetime import datetime
from functools import wraps
from typing import Callable, Optional, Any
from pathlib import Path

# Constants
DEFAULT_TIMEOUT_HOURS = 6
EXIT_CODE_TIMEOUT = 143
LOG_FILE_NAME = "timeout.log"

# Global start time tracking
_start_time: Optional[float] = None
_timeout_seconds: int = DEFAULT_TIMEOUT_HOURS * 3600

def setup_timeout_logging(log_dir: Optional[str] = None) -> logging.Logger:
    """
    Setup the timeout logger.
    
    Args:
        log_dir: Directory for log files. Defaults to 'logs' relative to project root.
        
    Returns:
        Configured logger instance.
    """
    if log_dir is None:
        # Default to 'logs' relative to project root
        # Assuming project root is two levels up from this file (code/src/utils/)
        project_root = Path(__file__).resolve().parent.parent.parent.parent
        log_dir = project_root / "logs"
    else:
        log_dir = Path(log_dir)
    
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / LOG_FILE_NAME
    
    logger = logging.getLogger("timeout_monitor")
    logger.setLevel(logging.WARNING)
    
    # Avoid adding duplicate handlers if called multiple times
    if not logger.handlers:
        handler = logging.FileHandler(log_path)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def set_global_timeout(timeout_hours: float = DEFAULT_TIMEOUT_HOURS) -> None:
    """
    Set the global timeout duration.
    
    Args:
        timeout_hours: Duration in hours before timeout.
    """
    global _timeout_seconds, _start_time
    _timeout_seconds = int(timeout_hours * 3600)
    _start_time = time.time()

def check_timeout(logger: Optional[logging.Logger] = None) -> bool:
    """
    Check if the global timeout has been exceeded.
    
    Args:
        logger: Logger instance to use for warnings.
        
    Returns:
        True if timeout exceeded, False otherwise.
    """
    if _start_time is None:
        return False
        
    elapsed = time.time() - _start_time
    if elapsed > _timeout_seconds:
        if logger is None:
            logger = setup_timeout_logging()
        logger.warning(
            f"Global timeout exceeded: {elapsed:.2f}s > {_timeout_seconds}s. "
            f"Exiting with code {EXIT_CODE_TIMEOUT}."
        )
        return True
    return False

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    logger = setup_timeout_logging()
    logger.warning(
        f"Timeout signal received. Exiting with code {EXIT_CODE_TIMEOUT}."
    )
    sys.exit(EXIT_CODE_TIMEOUT)

def enforce_timeout(timeout_hours: float = DEFAULT_TIMEOUT_HOURS):
    """
    Decorator to enforce timeout on a function.
    
    This sets up a signal handler that will trigger after the specified duration.
    If the timeout is exceeded, the function will be interrupted and the process
    will exit with code 143.
    
    Args:
        timeout_hours: Duration in hours before timeout.
        
    Returns:
        Decorator function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Set global start time if not already set
            global _start_time
            if _start_time is None:
                _start_time = time.time()
                _timeout_seconds = int(timeout_hours * 3600)
            
            # Register signal handler (Unix only)
            if hasattr(signal, 'SIGALRM'):
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(_timeout_seconds)
                try:
                    result = func(*args, **kwargs)
                finally:
                    signal.alarm(0)  # Cancel the alarm
                    signal.signal(signal.SIGALRM, old_handler)  # Restore old handler
                return result
            else:
                # Fallback for non-Unix systems: check timeout periodically
                logger = setup_timeout_logging()
                start = time.time()
                result = func(*args, **kwargs)
                elapsed = time.time() - start
                if elapsed > _timeout_seconds:
                    logger.warning(
                        f"Global timeout exceeded: {elapsed:.2f}s > {_timeout_seconds}s. "
                        f"Exiting with code {EXIT_CODE_TIMEOUT}."
                    )
                    sys.exit(EXIT_CODE_TIMEOUT)
                return result
        return wrapper
    return decorator

class TimeoutContext:
    """
    Context manager to enforce timeout within a block.
    
    Usage:
        with TimeoutContext(hours=6):
            # Your code here
            pass
    """
    def __init__(self, hours: float = DEFAULT_TIMEOUT_HOURS):
        self.timeout_seconds = int(hours * 3600)
        self.logger = setup_timeout_logging()
        
    def __enter__(self):
        global _start_time
        if _start_time is None:
            _start_time = time.time()
        
        # Register signal handler (Unix only)
        if hasattr(signal, 'SIGALRM'):
            self.old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.timeout_seconds)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)  # Cancel the alarm
            signal.signal(signal.SIGALRM, self.old_handler)  # Restore old handler
        
        # Check timeout even on exit
        if exc_type is None:
            elapsed = time.time() - _start_time if _start_time else 0
            if elapsed > self.timeout_seconds:
                self.logger.warning(
                    f"Global timeout exceeded: {elapsed:.2f}s > {self.timeout_seconds}s. "
                    f"Exiting with code {EXIT_CODE_TIMEOUT}."
                )
                sys.exit(EXIT_CODE_TIMEOUT)
        return False

def main():
    """
    Main function to demonstrate timeout enforcement.
    
    This function simulates a long-running process that checks timeout.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Timeout wrapper for pipeline execution")
    parser.add_argument(
        "--timeout-hours", 
        type=float, 
        default=DEFAULT_TIMEOUT_HOURS,
        help=f"Timeout duration in hours (default: {DEFAULT_TIMEOUT_HOURS})"
    )
    parser.add_argument(
        "--simulate-long-run",
        action="store_true",
        help="Simulate a long-running process for testing"
    )
    
    args = parser.parse_args()
    
    # Initialize timeout
    set_global_timeout(args.timeout_hours)
    logger = setup_timeout_logging()
    logger.info(f"Timeout set to {args.timeout_hours} hours ({_timeout_seconds} seconds)")
    
    if args.simulate_long_run:
        logger.info("Simulating long-running process...")
        try:
            with TimeoutContext(hours=args.timeout_hours):
                # Simulate work with periodic timeout checks
                for i in range(100):
                    time.sleep(0.1)  # Simulate work
                    if check_timeout(logger):
                        logger.warning("Timeout detected during work simulation.")
                        sys.exit(EXIT_CODE_TIMEOUT)
                logger.info("Work completed within timeout.")
        except SystemExit as e:
            if e.code == EXIT_CODE_TIMEOUT:
                raise
            logger.info(f"Process exited normally with code {e.code}")
    else:
        logger.info("Timeout wrapper initialized. Use --simulate-long-run to test.")

if __name__ == "__main__":
    main()
