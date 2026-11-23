"""
Logging configuration for the project.

Provides utilities for consistent logging, latency measurement, and memory monitoring.
"""

import logging
import sys
import os
import time
import traceback
import resource
from typing import Optional, Callable

def get_logger(name: str = "llmxive") -> logging.Logger:
    """
    Configures and returns a logger with a specific format.

    Args:
        name: The name of the logger.

    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    ch.setFormatter(formatter)
    
    logger.addHandler(ch)
    return logger

def log_latency(func: Callable) -> Callable:
    """Decorator to log the execution time of a function."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            end_time = time.time()
            elapsed = end_time - start_time
            logger = logging.getLogger(func.__module__)
            logger.info(f"Function '{func.__name__}' took {elapsed:.4f} seconds")
    return wrapper

def log_memory_usage(tag: str = "General") -> None:
    """
    Logs current memory usage of the process.

    Args:
        tag: A label to identify the memory snapshot.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    max_mem_mb = usage.ru_maxrss / 1024.0  # Convert KB to MB (on Linux)
    logger = logging.getLogger(__name__)
    logger.info(f"Memory Usage [{tag}]: Peak RSS = {max_mem_mb:.2f} MB")

def check_and_log_numerical_warnings(tensor: Optional[object] = None) -> None:
    """
    Checks a tensor for NaN or Inf values and logs warnings.

    Args:
        tensor: A tensor-like object (e.g., torch.Tensor, numpy.ndarray).
    """
    logger = logging.getLogger(__name__)
    if tensor is None:
        return
    
    try:
        if hasattr(tensor, 'isnan'):
            if tensor.isnan().any():
                logger.warning("NaN detected in tensor")
            if torch.isinf(tensor).any():
                logger.warning("Inf detected in tensor")
        elif hasattr(tensor, 'dtype'):
            # Numpy
            if np.isnan(tensor).any():
                logger.warning("NaN detected in numpy array")
            if np.isinf(tensor).any():
                logger.warning("Inf detected in numpy array")
    except Exception as e:
        logger.debug(f"Could not check numerical warnings: {e}")

# Context managers for timing and monitoring
class latency_timer:
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start = None
    
    def __enter__(self):
        self.start = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start
        logger = logging.getLogger(__name__)
        logger.info(f"{self.name} completed in {elapsed:.4f} seconds")

class memory_monitor:
    def __enter__(self):
        self.start_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_mem = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        delta_mem = (end_mem - self.start_mem) / 1024.0
        logger = logging.getLogger(__name__)
        logger.info(f"Memory delta: {delta_mem:.2f} MB")
