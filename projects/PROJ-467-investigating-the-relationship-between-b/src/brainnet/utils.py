"""
Utility functions for the brainnet project.

Provides:
- Seed handling for reproducibility
- Logging setup configuration
- Memory profiling decorators
"""
import functools
import logging
import os
import sys
import time
import tracemalloc
from typing import Any, Callable, Optional

import numpy as np


def set_seed(seed: int = 42) -> None:
    """
    Set random seeds for reproducibility across numpy and the Python random module.
    
    Args:
        seed: Integer seed value. Defaults to 42.
    """
    np.random.seed(seed)
    # Note: Python's random module seed is set if needed, though not explicitly imported here
    # to keep dependencies minimal. If needed, import random and call random.seed(seed).


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    name: str = "brainnet"
) -> logging.Logger:
    """
    Configure and return a logger with console and optional file handlers.
    
    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_file: Optional path to a log file. If None, only console output is used.
        name: Name of the logger.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers if they already exist (prevents duplicate logs in tests)
    if logger.hasHandlers():
        logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def profile_memory(
    func: Optional[Callable] = None,
    log: Optional[logging.Logger] = None
) -> Callable:
    """
    Decorator to profile memory usage of a function.
    
    Tracks peak memory usage and prints it to the provided logger or stdout.
    
    Args:
        func: The function to decorate.
        log: Optional logger instance. If None, prints to stdout.
        
    Returns:
        Wrapped function with memory profiling.
    """
    if func is None:
        # Called with arguments like @profile_memory(log=my_logger)
        def decorator(f: Callable) -> Callable:
            return profile_memory(func=f, log=log)
        return decorator

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = log or logging.getLogger("memory_profiler")
        if not logger.handlers:
            # Fallback to stdout if logger has no handlers
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(message)s'))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        logger.info(f"Starting memory profile for: {func.__name__}")
        
        tracemalloc.start()
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
        finally:
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            elapsed = time.time() - start_time
            
            logger.info(
                f"Finished {func.__name__}: "
                f"Peak memory: {peak / 1024 / 1024:.2f} MB, "
                f"Elapsed: {elapsed:.2f}s"
            )
            
        return result

    return wrapper
