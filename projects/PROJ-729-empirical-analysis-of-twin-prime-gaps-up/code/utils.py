"""
Utility Functions Module.

Provides logging setup, memory monitoring, and error handling.
"""

import sys
import logging
import resource
import time
from contextlib import contextmanager
from typing import Optional, Union

def setup_logging(level: Union[int, str] = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger.

    Parameters
    ----------
    level : int or str, optional
        If an integer, it is interpreted as a logging level (e.g., logging.INFO).
        If a string, it is interpreted as the logger name; the logging level
        defaults to INFO. This flexibility allows callers such as
        ``setup_logging("validate_schema")`` (which passes a name) to work
        without raising ``ValueError: Unknown level``.
    """
    # Determine if ``level`` is a logger name or a logging level.
    if isinstance(level, str):
        logger_name = level
        log_level = logging.INFO
    else:
        logger_name = None
        log_level = level

    # Configure the root logger only once.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    # Return the requested logger (named or root).
    return logging.getLogger(logger_name) if logger_name else logging.getLogger()

def get_memory_usage_mb() -> float:
    """
    Get the current peak memory usage of the process in MB.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in KB on Linux/macOS
    return usage.ru_maxrss / 1024.0

@contextmanager
def track_resources(label: str = "Operation"):
    """
    Context manager to track time and memory usage.
    """
    start_time = time.time()
    start_mem = get_memory_usage_mb()
    
    try:
        yield
    finally:
        end_time = time.time()
        end_mem = get_memory_usage_mb()
        duration = end_time - start_time
        mem_used = end_mem - start_mem
        
        logger = logging.getLogger(__name__)
        logger.info(f"{label} completed in {duration:.2f}s. Peak memory: {end_mem:.2f} MB")

def exit_with_error(message: str, code: int = 1) -> None:
    """
    Log an error message and exit with the specified code.
    """
    logger = logging.getLogger(__name__)
    logger.error(f"ERROR: {message}")
    sys.exit(code)
