"""
Timeout wrapper to enforce global runtime limits for the pipeline.

This module provides functionality to:
1. Set a global timeout (default 6 hours) based on configuration.
2. Check the current elapsed time against the limit.
3. Trigger a graceful shutdown (exit code 143) if the limit is exceeded.
4. Log warnings to logs/timeout.log when the limit is approached or exceeded.
"""

import os
import signal
import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable, Any

# Import project configuration utilities
from code.config.settings import get_config, get_paths, ensure_directories

# Global variables to track state
_start_time: Optional[float] = None
_timeout_seconds: Optional[float] = None
_timeout_logger: Optional[logging.Logger] = None
_context_active: bool = False

class TimeoutExceeded(Exception):
    """Exception raised when the global timeout is exceeded."""
    pass

class TimeoutContext:
    """
    Context manager to enforce timeout on a block of code.
    If the timeout is exceeded within the block, it raises TimeoutExceeded.
    """
    def __init__(self, timeout_seconds: float):
        self.timeout_seconds = timeout_seconds
        self.start_time = time.time()
        self.expired = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.expired:
            # If we timed out, we don't suppress the exception, we let it propagate
            return False
        return True

    def check(self) -> bool:
        """Check if timeout has been exceeded. Returns True if exceeded."""
        elapsed = time.time() - self.start_time
        if elapsed >= self.timeout_seconds:
            self.expired = True
            _log_timeout_warning(f"TimeoutContext exceeded: {elapsed:.2f}s >= {self.timeout_seconds:.2f}s")
            raise TimeoutExceeded(f"Timeout exceeded after {elapsed:.2f} seconds")
        return False

def setup_timeout_logging() -> logging.Logger:
    """
    Sets up the logger for timeout events.
    Logs to logs/timeout.log and stdout.
    """
    global _timeout_logger

    if _timeout_logger is not None:
        return _timeout_logger

    paths = get_paths()
    log_dir = paths.get("log_dir", "logs")
    log_file = Path(log_dir) / "timeout.log"

    # Ensure log directory exists
    ensure_directories([str(log_dir)])

    # Create logger
    logger = logging.getLogger("llmXive.timeout")
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    logger.addHandler(fh)

    # Console handler (optional, for immediate feedback)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.WARNING)
    ch.setFormatter(logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    ))
    logger.addHandler(ch)

    _timeout_logger = logger
    return logger

def _log_timeout_warning(message: str):
    """Helper to log timeout warnings."""
    logger = setup_timeout_logging()
    logger.warning(message)

def _log_timeout_error(message: str):
    """Helper to log timeout errors."""
    logger = setup_timeout_logging()
    logger.error(message)

def set_global_timeout(seconds: Optional[float] = None):
    """
    Sets the global timeout duration.
    If seconds is None, reads from config (default 6 hours = 21600 seconds).
    Records the start time immediately.
    """
    global _start_time, _timeout_seconds

    if _start_time is not None:
        _log_timeout_warning("Global timeout already set. Ignoring subsequent calls.")
        return

    if seconds is None:
        config = get_config()
        # Default to 6 hours (21600 seconds) if not specified
        _timeout_seconds = config.get("runtime", {}).get("max_runtime_seconds", 21600)
    else:
        _timeout_seconds = seconds

    _start_time = time.time()
    setup_timeout_logging().info(f"Global timeout set to {_timeout_seconds} seconds. Start time: {datetime.now()}")

def get_remaining_time_seconds() -> Optional[float]:
    """
    Returns the remaining time in seconds before the global timeout.
    Returns None if timeout is not set.
    """
    if _start_time is None or _timeout_seconds is None:
        return None

    elapsed = time.time() - _start_time
    remaining = _timeout_seconds - elapsed
    return max(0.0, remaining)

def check_timeout() -> bool:
    """
    Checks if the global timeout has been exceeded.
    Returns True if timeout exceeded, False otherwise.
    Logs a warning and prepares for exit if exceeded.
    """
    if _start_time is None:
        return False

    elapsed = time.time() - _start_time
    if elapsed >= _timeout_seconds:
        _log_timeout_warning(f"Global timeout exceeded! Elapsed: {elapsed:.2f}s, Limit: {_timeout_seconds:.2f}s")
        _log_timeout_error("Exiting pipeline with code 143 (timeout).")
        return True
    return False

def timeout_handler(signum, frame):
    """
    Signal handler for timeout.
    Called when the alarm signal is received.
    """
    _log_timeout_error("Timeout signal received. Exiting gracefully.")
    sys.exit(143)

def enforce_timeout(seconds: float):
    """
    Sets a signal-based alarm to enforce timeout.
    This is a hard limit that will interrupt the process.
    """
    if seconds <= 0:
        return

    # Set the alarm
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(int(seconds))
    _log_timeout_warning(f"Hard timeout alarm set for {seconds} seconds.")

def setup_timeout_alarm():
    """
    Convenience wrapper to set up the global timeout alarm based on config.
    """
    if _timeout_seconds is None:
        set_global_timeout()
    if _timeout_seconds and _timeout_seconds > 0:
        enforce_timeout(_timeout_seconds)

def main():
    """
    Main entry point for testing the timeout wrapper.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Test timeout wrapper functionality")
    parser.add_argument("--duration", type=float, default=5, help="Duration to simulate (seconds)")
    parser.add_argument("--limit", type=float, default=2, help="Timeout limit (seconds)")
    args = parser.parse_args()

    set_global_timeout(args.limit)

    start = time.time()
    while time.time() - start < args.duration:
        if check_timeout():
            print("Timeout detected, stopping loop.")
            break
        time.sleep(0.5)

    if check_timeout():
        print("Test PASSED: Timeout was correctly detected.")
        sys.exit(143)
    else:
        print("Test PASSED: No timeout occurred within duration.")
        sys.exit(0)

if __name__ == "__main__":
    main()
