"""
Utilities for the brainnet project.

This module provides:
- Seed handling for reproducibility
- Logging configuration
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
    Set the random seed for reproducibility.

    Args:
        seed: Integer seed value (default: 42).
    """
    np.random.seed(seed)
    # Optionally set other seeds if needed (e.g., torch, tensorflow)
    # For this project, we stick to numpy as per requirements.


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    name: str = "brainnet"
) -> logging.Logger:
    """
    Configure logging for the project.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to a log file. If None, logs to stdout.
        name: Logger name.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def profile_memory(
    logger_name: str = "brainnet",
    log_level: int = logging.INFO
) -> Callable:
    """
    Decorator to profile memory usage of a function.

    Logs peak memory usage (in MB) before and after function execution.

    Args:
        logger_name: Name of the logger to use for output.
        log_level: Logging level for the memory profile message.

    Returns:
        Decorated function.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = logging.getLogger(logger_name)

            # Start tracking
            tracemalloc.start()
            current, peak_before = tracemalloc.get_traced_memory()

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
            finally:
                # Stop tracking
                end_time = time.time()
                current, peak_after = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                elapsed = end_time - start_time
                # Calculate memory difference in MB
                memory_diff_mb = (peak_after - peak_before) / (1024 * 1024)
                peak_total_mb = peak_after / (1024 * 1024)

                logger.log(
                    log_level,
                    f"Memory Profile: '{func.__name__}' "
                    f"took {elapsed:.2f}s, "
                    f"peak memory: {peak_total_mb:.2f} MB, "
                    f"delta: {memory_diff_mb:.2f} MB"
                )

            return result
        return wrapper
    return decorator