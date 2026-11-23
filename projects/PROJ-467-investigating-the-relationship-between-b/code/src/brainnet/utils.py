"""
Utility functions for the brainnet project.

Includes:
- Seed setting for reproducibility
- Logging setup
- Memory profiling decorator
"""
import functools
import logging
import os
import sys
import time
import tracemalloc
from typing import Optional

import numpy as np


def set_seed(seed: int = 42) -> None:
    """
    Set the random seed for reproducibility.
    
    Args:
        seed: Integer seed value.
    """
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # If using torch, would need: torch.manual_seed(seed)
    # If using tensorflow, would need: tf.random.set_seed(seed)


def setup_logging(name: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Setup logging configuration and return a logger instance.
    
    Args:
        name: Name of the logger (usually __name__).
        level: Logging level (default: INFO).
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times if called repeatedly
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def profile_memory(func):
    """
    Decorator to profile memory usage of a function.
    
    Logs peak memory usage in MB after function execution.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tracemalloc.start()
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
        finally:
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            elapsed = time.time() - start_time
            
            logger = logging.getLogger(func.__module__)
            logger.info(
                f"Function '{func.__name__}' executed in {elapsed:.2f}s. "
                f"Peak memory usage: {peak / 1024 / 1024:.2f} MB"
            )
            
        return result
    return wrapper
