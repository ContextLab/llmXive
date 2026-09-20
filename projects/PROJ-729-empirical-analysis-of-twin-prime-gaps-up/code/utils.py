"""
Utility Functions Module.

Provides logging setup, memory monitoring, and error handling.
"""

import sys
import logging
import resource
import time
from contextlib import contextmanager
from typing import Optional

def setup_logging(level=logging.INFO) -> logging.Logger:
    """
    Configure and return the root logger.
    """
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger()

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
