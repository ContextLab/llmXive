"""
Logging infrastructure for the llmXive coral resilience pipeline.

Provides utilities to:
- Configure project-wide loggers with consistent formatting.
- Track memory usage (RSS) via the `psutil` library.
- Measure and log execution time for pipeline stages.

This module implements the requirements for task T005.
"""
import os
import sys
import time
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import resource

# Attempt to import psutil for more accurate memory tracking if available,
# otherwise fall back to resource (Unix) or a no-op fallback.
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    format_str: Optional[str] = None
) -> logging.Logger:
    """
    Configure and return a logger with file and console handlers.
    
    Args:
        name: Logger name (e.g., 'pipeline.ingest').
        log_file: Optional path to a log file. If None, only console output is used.
        level: Logging level (default: INFO).
        format_str: Custom format string. Defaults to a standard pipeline format.
        
    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    if format_str is None:
        format_str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    
    formatter = logging.Formatter(format_str, datefmt="%Y-%m-%d %H:%M:%S")
    
    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    ch.setLevel(level)
    logger.addHandler(ch)
    
    # File Handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        fh.setLevel(level)
        logger.addHandler(fh)
    
    return logger


def get_memory_usage_mb() -> float:
    """
    Get the current Resident Set Size (RSS) memory usage in MB.
    
    Tries `psutil` first for cross-platform accuracy, falls back to 
    `resource` (Unix only) if available, otherwise returns 0.0.
    
    Returns:
        Memory usage in Megabytes.
    """
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    
    try:
        # Unix/Linux/MacOS specific
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in kilobytes on Linux/macOS
        return usage.ru_maxrss / 1024.0
    except AttributeError:
        # Windows or other OS where resource doesn't have getrusage
        return 0.0


def log_memory_usage(logger: logging.Logger, message: str = "Current memory usage") -> float:
    """
    Log the current memory usage and return the value.
    
    Args:
        logger: The logger instance to use.
        message: Prefix message for the log entry.
        
    Returns:
        Current memory usage in MB.
    """
    mb = get_memory_usage_mb()
    logger.info(f"{message}: {mb:.2f} MB")
    return mb


class MemoryTracker:
    """
    Context manager to track memory usage at the start and end of a block.
    """
    def __init__(self, logger: logging.Logger, description: str = "Block"):
        self.logger = logger
        self.description = description
        self.start_mb: float = 0.0
        self.end_mb: float = 0.0
    
    def __enter__(self):
        self.start_mb = get_memory_usage_mb()
        self.logger.info(f"[Memory] Start: {self.description} -> {self.start_mb:.2f} MB")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_mb = get_memory_usage_mb()
        delta = self.end_mb - self.start_mb
        self.logger.info(
            f"[Memory] End: {self.description} -> {self.end_mb:.2f} MB "
            f"(Delta: {delta:+.2f} MB)"
        )
        return False


class ExecutionTimer:
    """
    Context manager to track and log execution time.
    """
    def __init__(self, logger: logging.Logger, description: str = "Block"):
        self.logger = logger
        self.description = description
        self.start_time: float = 0.0
        self.end_time: float = 0.0
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.info(f"[Time] Start: {self.description}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        self.logger.info(
            f"[Time] End: {self.description} -> Duration: {duration:.2f} seconds"
        )
        return False


def log_execution_time(
    logger: logging.Logger, 
    start_time: float, 
    message: str = "Operation completed"
) -> float:
    """
    Calculate and log the duration since a start time.
    
    Args:
        logger: Logger instance.
        start_time: Unix timestamp from time.time().
        message: Message to log with the duration.
        
    Returns:
        Duration in seconds.
    """
    duration = time.time() - start_time
    logger.info(f"{message}: {duration:.2f} seconds")
    return duration
