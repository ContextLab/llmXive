"""
Utility functions for memory monitoring, logging, and error handling.
"""
import os
import sys
import resource
import logging
from pathlib import Path
from typing import Optional

from config import MEMORY_LIMIT_GB

class PipelineError(Exception):
    """Custom exception for pipeline-related errors."""
    pass

def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger instance.

    Args:
        log_file: Optional path to a log file. If None, logs to stderr.
        level: Logging level (default: INFO).

    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger("pipeline")
    logger.setLevel(level)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Always add a stream handler to stderr
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger

def get_current_memory_gb() -> float:
    """
    Get the current memory usage of the process in GB.

    Returns:
        Current memory usage in GB.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # maxrss is in KB on Linux/macOS
    return usage.ru_maxrss / (1024 * 1024)

def get_peak_memory_gb() -> float:
    """
    Get the peak memory usage of the process in GB.

    Returns:
        Peak memory usage in GB.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return usage.ru_maxrss / (1024 * 1024)

def check_memory_limit(limit_gb: float = MEMORY_LIMIT_GB) -> None:
    """
    Check if the current memory usage exceeds the specified limit.

    Args:
        limit_gb: Memory limit in GB (default: from config).

    Raises:
        MemoryError: If current memory usage exceeds the limit.
    """
    current = get_current_memory_gb()
    if current > limit_gb:
        raise MemoryError(
            f"Current memory usage ({current:.2f} GB) exceeds limit ({limit_gb} GB)."
        )

def log_peak_memory() -> None:
    """
    Log the peak memory usage to stderr.
    """
    peak = get_peak_memory_gb()
    sys.stderr.write(f"Peak memory usage: {peak:.2f} GB\n")
    sys.stderr.flush()
