"""
Logging infrastructure for the llmXive research pipeline.

Provides:
- A configured root logger with file and console handlers.
- Runtime tracking: logs start/end times and total duration.
- Integration with timeout_wrapper for unified logging.
"""
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Ensure we can import from the project root if needed, though relative imports
# are preferred for internal modules.
try:
    from code.src.utils.timeout_wrapper import setup_timeout_logging
except ImportError:
    # Fallback if run in a context where code/ is not in sys.path
    # This should be handled by the project setup, but we guard against it.
    pass


LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "pipeline.log"
TIMEOUT_LOG_FILE = LOG_DIR / "timeout.log"

_logger: Optional[logging.Logger] = None
_start_time: Optional[float] = None
_runtime_handler: Optional[logging.Handler] = None


def _ensure_log_dir():
    """Create the logs directory if it doesn't exist."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve or create the project logger.

    If name is None, returns the root logger configured for this project.
    If name is provided, returns a child logger.
    """
    global _logger

    if _logger is None:
        _ensure_log_dir()

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # Remove existing handlers to avoid duplicates on re-import
        root_logger.handlers.clear()

        # File handler
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)

        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

        _logger = root_logger

    if name:
        return _logger.getChild(name)
    return _logger


def start_runtime_tracking():
    """
    Initialize runtime tracking.
    Logs the start time and attaches a handler to track total duration.
    """
    global _start_time, _runtime_handler

    logger = get_logger()
    _start_time = time.time()
    start_dt = datetime.now().isoformat()

    logger.info(f"Pipeline execution started at {start_dt}")

    # We don't strictly need a separate handler for runtime tracking if we just
    # calculate duration at the end, but we can add a custom formatter or logic
    # if needed. For now, we rely on the start/end log messages.


def stop_runtime_tracking():
    """
    Finalize runtime tracking.
    Calculates total duration and logs it.
    """
    global _start_time

    if _start_time is None:
        logger = get_logger()
        logger.warning("Runtime tracking was not started. Cannot calculate duration.")
        return

    end_time = time.time()
    duration_seconds = end_time - _start_time
    duration_minutes = duration_seconds / 60.0
    end_dt = datetime.now().isoformat()

    logger = get_logger()
    logger.info(f"Pipeline execution ended at {end_dt}")
    logger.info(f"Total runtime: {duration_seconds:.2f} seconds ({duration_minutes:.2f} minutes)")

    # Reset start time
    _start_time = None


def log_runtime_stats():
    """
    Helper to log runtime statistics if tracking has been active.
    Useful for periodic checks or at specific checkpoints.
    """
    if _start_time is not None:
        current_time = time.time()
        elapsed = current_time - _start_time
        logger = get_logger()
        logger.info(f"Current runtime checkpoint: {elapsed:.2f} seconds elapsed so far.")


def setup_pipeline_logging():
    """
    Convenience function to initialize the full logging infrastructure.
    Calls setup_timeout_logging (from timeout_wrapper) and start_runtime_tracking.
    """
    # Ensure timeout logging is set up (creates logs/timeout.log)
    try:
        setup_timeout_logging()
    except Exception as e:
        # If setup_timeout_logging fails (e.g. import issue), we still want
        # our main logger to work, so we log a warning but don't crash.
        print(f"Warning: Could not setup timeout logging: {e}")

    start_runtime_tracking()
    return get_logger()


def main():
    """
    Entry point for testing the logger module directly.
    """
    logger = setup_pipeline_logging()

    logger.info("Testing log message levels...")
    logger.debug("This is a debug message (might not show depending on level).")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")

    # Simulate some work
    time.sleep(1)
    log_runtime_stats()

    stop_runtime_tracking()
    print("Logging test completed. Check logs/pipeline.log for output.")


if __name__ == "__main__":
    main()
