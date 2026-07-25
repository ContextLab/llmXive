"""
Timeout wrapper to enforce global 6h runtime limit (FR-013).

This module provides functionality to:
1. Set a global timeout for the entire pipeline execution
2. Check if the timeout has been exceeded
3. Handle timeout events gracefully (log warning, exit with code 143)
4. Allow skipping remaining PRs when timeout is reached
"""

import os
import signal
import sys
import time
import logging
from datetime import datetime
from typing import Optional, Callable, Any

# Global timeout configuration
GLOBAL_TIMEOUT_SECONDS = 6 * 60 * 60  # 6 hours in seconds
TIMEOUT_LOG_FILE = "logs/timeout.log"

# Global state
_start_time: Optional[float] = None
_logger: Optional[logging.Logger] = None
_timeout_handler_installed = False


def setup_timeout_logging() -> logging.Logger:
    """
    Setup logging for timeout events.
    
    Returns:
        logging.Logger: Configured logger for timeout events
    """
    global _logger
    
    if _logger is not None:
        return _logger
    
    # Ensure logs directory exists
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Create logger
    _logger = logging.getLogger("timeout")
    _logger.setLevel(logging.WARNING)
    
    # Remove existing handlers to avoid duplicates
    _logger.handlers = []
    
    # File handler for timeout.log
    file_handler = logging.FileHandler(TIMEOUT_LOG_FILE)
    file_handler.setLevel(logging.WARNING)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_format)
    _logger.addHandler(file_handler)
    
    # Also log to console at WARNING level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(file_format)
    _logger.addHandler(console_handler)
    
    return _logger


def set_global_timeout() -> None:
    """
    Set the global timeout start time.
    
    This should be called once at the beginning of the pipeline execution.
    """
    global _start_time
    _start_time = time.time()
    logger = setup_timeout_logging()
    logger.info(f"Global timeout set to {GLOBAL_TIMEOUT_SECONDS} seconds (6 hours)")
    logger.info(f"Pipeline started at {datetime.now().isoformat()}")


def check_timeout() -> bool:
    """
    Check if the global timeout has been exceeded.
    
    Returns:
        bool: True if timeout has been exceeded, False otherwise
    """
    if _start_time is None:
        # If timeout wasn't initialized, assume no timeout
        return False
    
    elapsed = time.time() - _start_time
    if elapsed > GLOBAL_TIMEOUT_SECONDS:
        return True
    return False


def timeout_handler(signum: int, frame: Any) -> None:
    """
    Signal handler for timeout events.
    
    Args:
        signum: Signal number
        frame: Current stack frame
    """
    logger = setup_timeout_logging()
    logger.warning(f"TIMEOUT EXCEEDED: Pipeline execution exceeded {GLOBAL_TIMEOUT_SECONDS} seconds")
    logger.warning(f"Timeout occurred at {datetime.now().isoformat()}")
    logger.warning("Gracefully skipping remaining PRs and exiting with code 143")
    
    # Log runtime stats before exiting
    if _start_time:
        elapsed = time.time() - _start_time
        logger.warning(f"Total runtime: {elapsed:.2f} seconds ({elapsed/3600:.2f} hours)")
    
    # Exit with code 143 (128 + 15, where 15 is SIGTERM)
    sys.exit(143)


def enforce_timeout() -> None:
    """
    Enforce the global timeout by setting up signal handlers and checking elapsed time.
    
    This function:
    1. Sets up SIGALRM signal handler (Unix only)
    2. Sets a timer for the global timeout
    3. Checks if timeout has been exceeded
    """
    global _timeout_handler_installed
    
    if _timeout_handler_installed:
        return
    
    logger = setup_timeout_logging()
    
    # Set up signal handler for Unix systems
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, timeout_handler)
        # Set alarm for GLOBAL_TIMEOUT_SECONDS
        signal.alarm(GLOBAL_TIMEOUT_SECONDS)
        _timeout_handler_installed = True
        logger.info("SIGALRM timeout handler installed")
    else:
        # For non-Unix systems (Windows), we'll rely on periodic checks
        logger.warning("SIGALRM not available (Windows), using periodic timeout checks")
        _timeout_handler_installed = True
    
    # Also check elapsed time immediately
    if check_timeout():
        logger.warning("Timeout exceeded at startup!")
        timeout_handler(0, None)


class TimeoutContext:
    """
    Context manager for timeout-aware operations.
    
    Usage:
        with TimeoutContext():
            # Your code here
            # If timeout is exceeded, this will be skipped
            process_pr(pr)
    """
    
    def __enter__(self) -> 'TimeoutContext':
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        # Don't suppress exceptions
        return False
    
    def is_timeout_reached(self) -> bool:
        """
        Check if timeout has been reached within this context.
        
        Returns:
            bool: True if timeout exceeded, False otherwise
        """
        if check_timeout():
            logger = setup_timeout_logging()
            logger.warning("Timeout reached during operation")
            return True
        return False


def main() -> None:
    """
    Main function to demonstrate timeout wrapper usage.
    
    This sets up the global timeout and provides an example of how to use it.
    """
    # Set up global timeout
    set_global_timeout()
    enforce_timeout()
    
    logger = setup_timeout_logging()
    logger.info("Timeout wrapper initialized")
    
    # Example usage
    example_prs = [f"PR-{i}" for i in range(1, 11)]
    
    for pr in example_prs:
        if check_timeout():
            logger.warning(f"Timeout exceeded before processing {pr}")
            logger.warning("Skipping remaining PRs")
            break
        
        logger.info(f"Processing {pr}")
        # Simulate processing
        time.sleep(0.1)
    
    logger.info("Pipeline completed or timed out")

if __name__ == "__main__":
    main()
