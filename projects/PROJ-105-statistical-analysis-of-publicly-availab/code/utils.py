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

# Global logger instance configured at import time
_logger: Optional[logging.Logger] = None

def _get_or_create_logger() -> logging.Logger:
    """
    Returns the global logger, initializing it if necessary.
    Initializes logging to data/logs/pipeline.log at INFO level.
    """
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if called multiple times
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # File handler for data/logs/pipeline.log
        log_path = Path("data/logs/pipeline.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Stream handler for stderr
        stream_handler = logging.StreamHandler(sys.stderr)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        _logger = logger

    return _logger

def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger instance.

    If log_file is provided, it configures the global logger to write to that file.
    If log_file is None, it returns the pre-configured global logger (writing to data/logs/pipeline.log).
    
    Args:
        log_file: Optional path to a custom log file. If None, uses the default pipeline.log.
        level: Logging level (default: INFO).

    Returns:
        A configured logger instance.
    """
    logger = _get_or_create_logger()
    
    # If a custom log file is requested, ensure the global logger has that handler
    # Note: The global logger is already initialized to data/logs/pipeline.log by default.
    # If the user passes a different path, we add a handler for it without removing the default.
    if log_file and log_file != Path("data/logs/pipeline.log"):
        if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(log_file) for h in logger.handlers):
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    logger.setLevel(level)
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
