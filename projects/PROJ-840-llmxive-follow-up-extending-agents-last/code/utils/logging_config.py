"""
Logging infrastructure for the llmXive pipeline.

Provides configuration for capturing timeouts, memory usage, and general
execution logs with structured JSON output suitable for analysis.
"""

import logging
import os
import sys
import time
import threading
import json
import resource
from pathlib import Path
from typing import Optional, Dict, Any, Callable
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Try to import psutil for accurate memory monitoring if available
# It is listed in requirements.txt (via scikit-learn/pandas ecosystem)
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


# Constants
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_DIR = Path("data/logs")
DEFAULT_LOG_FILE = "pipeline.log"
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10MB
DEFAULT_BACKUP_COUNT = 5


class MemoryUsageHandler(logging.Handler):
    """
    A custom logging handler that captures memory usage at the time of log record creation.
    It appends memory stats (RSS, VMS) to the log record's extra fields.
    """

    def __init__(self, logger_name: str = "llmxive"):
        super().__init__()
        self.logger_name = logger_name

    def emit(self, record: logging.LogRecord):
        if HAS_PSUTIL:
            process = psutil.Process(os.getpid())
            mem_info = process.memory_info()
            record.memory_rss_mb = mem_info.rss / (1024 * 1024)
            record.memory_vms_mb = mem_info.vms / (1024 * 1024)
        else:
            # Fallback if psutil is not installed
            try:
                usage = resource.getrusage(resource.RUSAGE_SELF)
                record.memory_rss_mb = usage.ru_maxrss / 1024  # KB to MB on Linux
                record.memory_vms_mb = None
            except Exception:
                record.memory_rss_mb = None
                record.memory_vms_mb = None


class TimeoutMonitor:
    """
    Context manager and utility to enforce timeouts and log timeout events.
    """

    def __init__(self, timeout_seconds: float, logger: Optional[logging.Logger] = None):
        self.timeout_seconds = timeout_seconds
        self.logger = logger or get_logger()
        self.start_time: Optional[float] = None
        self.timer_thread: Optional[threading.Thread] = None
        self.timed_out = False

    def _check_timeout(self):
        if time.time() - self.start_time > self.timeout_seconds:
            self.timed_out = True
            self.logger.error(
                f"TIMEOUT: Operation exceeded {self.timeout_seconds}s limit.",
                extra={
                    "event": "timeout",
                    "duration_seconds": time.time() - self.start_time,
                    "threshold_seconds": self.timeout_seconds
                }
            )
            # Raise an exception to stop execution if desired, or just log
            raise TimeoutError(f"Operation timed out after {self.timeout_seconds} seconds")

    def __enter__(self):
        self.start_time = time.time()
        self.timer_thread = threading.Thread(target=self._check_timeout, daemon=True)
        self.timer_thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.timer_thread:
            self.timer_thread.join(timeout=0.1)
        if self.timed_out:
            # Prevent the TimeoutError from propagating if we want to handle it elsewhere,
            # but usually we want it to propagate. Let it propagate.
            return False
        return False


def get_memory_usage() -> Dict[str, Any]:
    """
    Returns a dictionary with current memory usage statistics.
    """
    result: Dict[str, Any] = {}
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        mem = process.memory_info()
        result = {
            "rss_mb": mem.rss / (1024 * 1024),
            "vms_mb": mem.vms / (1024 * 1024),
            "percent": process.memory_percent()
        }
    else:
        try:
            usage = resource.getrusage(resource.RUSAGE_SELF)
            result = {
                "rss_mb": usage.ru_maxrss / 1024,
                "vms_mb": None,
                "percent": None
            }
        except Exception:
            result = {"error": "Could not retrieve memory usage"}
    return result


def setup_logging(
    log_level: int = DEFAULT_LOG_LEVEL,
    log_dir: Optional[Path] = None,
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Configures the root logger and a module-specific logger for the pipeline.

    Args:
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_dir: Directory to store log files. Defaults to data/logs.
        log_file: Name of the log file. Defaults to pipeline.log.
        console_output: Whether to log to stdout.

    Returns:
        The configured 'llmxive' logger instance.
    """
    if log_dir is None:
        log_dir = DEFAULT_LOG_DIR
    if log_file is None:
        log_file = DEFAULT_LOG_FILE

    # Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / log_file

    # Create logger
    logger = logging.getLogger("llmxive")
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Formatter with JSON-like structure for easier parsing later
    # Using a custom format string that includes memory if available
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File Handler
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=DEFAULT_MAX_BYTES,
        backupCount=DEFAULT_BACKUP_COUNT
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Memory Usage Handler (Custom)
    mem_handler = MemoryUsageHandler()
    mem_handler.setLevel(log_level)
    # We attach memory info to the record, but we need a formatter that prints it
    mem_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s [RSS: %(memory_rss_mb)s MB]',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    mem_handler.setFormatter(mem_formatter)
    logger.addHandler(mem_handler)

    # Console Handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logger.info("Logging infrastructure initialized.")
    logger.info(f"Log file: {log_path}")

    return logger


def get_logger(name: str = "llmxive") -> logging.Logger:
    """
    Retrieves a logger instance.
    """
    return logging.getLogger(name)


def log_timeout_event(duration: float, threshold: float, message: str = ""):
    """
    Convenience function to log a timeout event manually.
    """
    logger = get_logger()
    logger.error(
        f"TIMEOUT: {message} | Duration: {duration:.2f}s | Threshold: {threshold:.2f}s",
        extra={"event": "timeout", "duration_seconds": duration, "threshold_seconds": threshold}
    )


def main():
    """
    Entry point for testing the logging configuration.
    Simulates a task with memory usage and a timeout.
    """
    logger = setup_logging(log_level=logging.DEBUG)

    logger.info("Starting simulated pipeline execution.")
    logger.debug("Debugging memory usage check.")
    logger.info(f"Current memory: {get_memory_usage()}")

    # Simulate a long-running task
    try:
        with TimeoutMonitor(timeout_seconds=2.0, logger=logger):
            logger.info("Task started, sleeping for 3 seconds to trigger timeout...")
            time.sleep(3.0)
    except TimeoutError as e:
        logger.error(f"Caught timeout error: {e}")
        logger.info(f"Memory at failure: {get_memory_usage()}")

    logger.info("Pipeline execution finished.")


if __name__ == "__main__":
    main()