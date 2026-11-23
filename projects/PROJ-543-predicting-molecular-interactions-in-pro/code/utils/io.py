import os
import sys
import time
import logging
import traceback
import resource
from contextlib import contextmanager
from typing import Optional, Callable, Any
from pathlib import Path
from dataclasses import dataclass, field
import json

# Project root relative to this file (utils/io.py is in code/utils/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Configuration constants
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FILE = "pipeline.log"
MEMORY_LIMIT_GB = 7.0
MEMORY_LIMIT_MB = MEMORY_LIMIT_GB * 1024
TIMEOUT_SECONDS = 3.5 * 3600  # 3.5 hours for T013 streaming

@dataclass
class MemoryStats:
    """Container for memory statistics."""
    current_mb: float
    peak_mb: float
    limit_mb: float
    timestamp: float

    def to_dict(self) -> dict:
        return {
            "current_mb": self.current_mb,
            "peak_mb": self.peak_mb,
            "limit_mb": self.limit_mb,
            "timestamp": self.timestamp
        }

class MemoryTracker:
    """
    Tracks memory usage over time and logs it.
    Implements SC-005: Fail loudly if memory exceeds 7GB.
    """
    def __init__(self, limit_mb: float = MEMORY_LIMIT_MB, logger: Optional[logging.Logger] = None):
        self.limit_mb = limit_mb
        self.logger = logger or get_logger("memory_tracker")
        self.start_time = time.time()
        self.samples: list[MemoryStats] = []
        self._peak_mb = 0.0

    def get_current_mb(self) -> float:
        """Get current RSS memory usage in MB."""
        usage = resource.getrusage(resource.RUSAGE_SELF)
        return usage.ru_maxrss / 1024.0  # Convert KB to MB (Linux/macOS)

    def sample(self) -> MemoryStats:
        """Record a memory sample and check limits."""
        current = self.get_current_mb()
        if current > self._peak_mb:
            self._peak_mb = current

        stats = MemoryStats(
            current_mb=current,
            peak_mb=self._peak_mb,
            limit_mb=self.limit_mb,
            timestamp=time.time()
        )
        self.samples.append(stats)

        if current > self.limit_mb:
            self.logger.error(
                f"MEMORY LIMIT EXCEEDED: Current {current:.2f} MB > Limit {self.limit_mb:.2f} MB. "
                f"Peak was {self._peak_mb:.2f} MB. Aborting pipeline."
            )
            raise MemoryError(f"Memory limit exceeded: {current:.2f} MB > {self.limit_mb:.2f} MB")

        self.logger.debug(f"Memory sample: {current:.2f} MB (Peak: {self._peak_mb:.2f} MB)")
        return stats

    def report(self) -> dict:
        """Generate a summary report of memory usage."""
        if not self.samples:
            self.sample()
        return {
            "duration_seconds": time.time() - self.start_time,
            "peak_mb": self._peak_mb,
            "limit_mb": self.limit_mb,
            "samples_count": len(self.samples),
            "final_sample": self.samples[-1].to_dict() if self.samples else None
        }

def setup_logging(
    log_file: Optional[str] = None,
    level: int = DEFAULT_LOG_LEVEL,
    project_root: Optional[Path] = None
) -> logging.Logger:
    """
    Configure the root logger for the project.
    Creates a log file in the project root's data/results directory if not specified.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # File handler
    log_path = Path(log_file) if log_file else (project_root or _PROJECT_ROOT) / "data" / "results" / DEFAULT_LOG_FILE
    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_path, mode='a')
    file_handler.setLevel(level)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)

    return root_logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)

def get_memory_usage_mb() -> float:
    """Return current memory usage in MB."""
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / 1024.0

def check_memory_limit(limit_mb: float = MEMORY_LIMIT_MB) -> bool:
    """
    Check if current memory usage is within limits.
    Returns True if OK, raises MemoryError if exceeded.
    """
    current = get_memory_usage_mb()
    if current > limit_mb:
        raise MemoryError(f"Memory limit {limit_mb} MB exceeded. Current: {current:.2f} MB")
    return True

@contextmanager
def timed_block(block_name: str, logger: Optional[logging.Logger] = None):
    """
    Context manager to time a block of code.
    Logs start, end, and duration.
    """
    log = logger or get_logger("timer")
    start = time.time()
    log.info(f"Starting: {block_name}")
    try:
        yield
    finally:
        duration = time.time() - start
        log.info(f"Completed: {block_name} in {duration:.2f} seconds")

def timed_function(func: Callable) -> Callable:
    """Decorator to time a function execution."""
    def wrapper(*args, **kwargs):
        log = get_logger("timer")
        start = time.time()
        log.info(f"Starting function: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start
            log.info(f"Finished function: {func.__name__} in {duration:.2f} seconds")
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper

def log_exception(exc: Exception, context: str = "An error occurred") -> None:
    """
    Log an exception with full traceback.
    Used for fail-loudly behavior.
    """
    log = get_logger("exception_handler")
    log.error(f"{context}: {exc}")
    log.error("Traceback:")
    for line in traceback.format_tb(exc.__traceback__):
        log.error(line.strip())
    log.error(f"Exception Type: {type(exc).__name__}")
    log.error(f"Exception Message: {str(exc)}")

def save_timing_report(report_data: dict, output_path: Optional[str] = None) -> Path:
    """
    Save timing and memory report to a JSON file.
    Default path: data/results/timing_report.json
    """
    if output_path is None:
        output_path = _PROJECT_ROOT / "data" / "results" / "timing_report.json"
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    return path