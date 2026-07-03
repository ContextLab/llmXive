import sys
import logging
import resource
import time
from contextlib import contextmanager
from typing import Optional

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return the project logger.
    """
    logger = logging.getLogger("llmXive")
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

def get_memory_usage_mb() -> float:
    """
    Returns the current memory usage of the process in MB.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is in kilobytes on Linux/macOS
    return usage.ru_maxrss / 1024.0

@contextmanager
def track_resources(name: str = "operation"):
    """
    Context manager to track execution time and peak memory usage.
    Yields a dict with 'elapsed_seconds' and 'peak_memory_mb'.
    """
    start_time = time.time()
    start_mem = get_memory_usage_mb()
    peak_mem = start_mem
    
    try:
        yield {
            "elapsed_seconds": 0.0,
            "peak_memory_mb": 0.0
        }
    finally:
        elapsed = time.time() - start_time
        current_mem = get_memory_usage_mb()
        peak_mem = max(start_mem, current_mem)
        
        # Update the yielded dict if it was used, or just log
        logging.getLogger("llmXive").info(
            f"{name}: {elapsed:.2f}s elapsed, Peak Memory: {peak_mem:.2f} MB"
        )

def exit_with_error(message: str, code: int = 1):
    """
    Log an error message and exit with the specified code.
    """
    logger = logging.getLogger("llmXive")
    logger.error(message)
    sys.exit(code)
