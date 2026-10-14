"""
Utility functions for the project, including logging setup,
array validation, safe division, MNE cache cleanup, and a flexible
execution time logger decorator.
"""
import os
import logging
import time
import functools
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, TypeVar, Union

import numpy as np

T = TypeVar('T')

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with console and optional file output.

    Args:
        name: Logger name (typically __name__).
        log_file: Optional path to log file.
        level: Logging level.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (optional)
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def validate_array_shape(arr: np.ndarray, expected_shape: Optional[tuple] = None,
                         min_dims: int = 1, max_dims: int = 3) -> bool:
    """
    Validate that a numpy array has the expected shape or dimensions.

    Args:
        arr: The array to validate.
        expected_shape: Optional tuple of expected dimensions.
        min_dims: Minimum number of dimensions allowed.
        max_dims: Maximum number of dimensions allowed.

    Returns:
        True if valid, raises ValueError otherwise.
    """
    if not isinstance(arr, np.ndarray):
        raise ValueError("Input must be a NumPy array.")
    if arr.ndim < min_dims or arr.ndim > max_dims:
        raise ValueError(f"Array must have between {min_dims} and {max_dims} dimensions; got {arr.ndim}.")
    if expected_shape and arr.shape != expected_shape:
        raise ValueError(f"Array shape {arr.shape} does not match expected {expected_shape}.")
    return True

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Perform safe division, returning a default value if denominator is zero.

    Args:
        numerator: The numerator.
        denominator: The denominator.
        default: Value to return if denominator is zero.

    Returns:
        The result of division or the default value.
    """
    try:
        return numerator / denominator if denominator != 0 else default
    except Exception:
        return default

def cleanup_mne_cache(cache_dir: Optional[str] = None) -> int:
    """
    Clean up MNE-Python cache directories to free disk space.

    Args:
        cache_dir: Optional specific cache directory.
                   If None, uses MNE's default cache location.

    Returns:
        Number of files removed.
    """
    import mne
    cache_path = Path(cache_dir) if cache_dir else Path(mne.utils.get_config('MNE_CACHE_DIR', default='~/.mne'))
    removed = 0
    if cache_path.is_dir():
        for file in cache_path.iterdir():
            try:
                file.unlink()
                removed += 1
            except Exception:
                pass
    return removed

def log_execution_time(func: Optional[Callable[..., T]] = None) -> Callable[..., T]:
    """
    Decorator to log the execution time of a function.
    Can be used with or without parentheses:
    - @log_execution_time
    - @log_execution_time()
    """
    if func is None:
        # Called with parentheses
        def decorator(real_func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(real_func)
            def wrapper(*args, **kwargs):
                start = time.time()
                result = real_func(*args, **kwargs)
                duration = time.time() - start
                logger = logging.getLogger(real_func.__module__)
                logger.info(f"Execution time for {real_func.__name__}: {duration:.2f}s")
                return result
            return wrapper
        return decorator
    else:
        # Called without parentheses
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start
            logger = logging.getLogger(func.__module__)
            logger.info(f"Execution time for {func.__name__}: {duration:.2f}s")
            return result
        return wrapper

def validate_pipeline_config(config: Dict[str, Any]) -> bool:
    """
    Validate that the pipeline configuration contains required keys and valid values.

    Args:
        config: The configuration dictionary.

    Returns:
        True if valid, raises ValueError otherwise.
    """
    required_keys = ['dataset_id', 'paths', 'filter', 'epoch', 'ica', 'channels']
    missing = [k for k in required_keys if k not in config]
    if missing:
        raise ValueError(f"Missing required config keys: {missing}")
    # Additional validation can be added here
    return True

def find_files_by_extension(directory: Union[str, Path], extension: str) -> List[Path]:
    """
    Recursively find all files with a given extension in a directory.

    Args:
        directory: Directory to search.
        extension: File extension (e.g., '.fif', '.csv').

    Returns:
        List of Path objects for matching files.
    """
    directory = Path(directory)
    return list(directory.rglob(f"*{extension}"))

def get_memory_usage_gb() -> float:
    """
    Get current memory usage in GB.

    Returns:
        Current memory usage in gigabytes.
    """
    import psutil
    process = psutil.Process(os.getpid())
    mem_bytes = process.memory_info().rss
    return mem_bytes / (1024 ** 3)

def main() -> None:
    """Main entry point for cleanup utilities when run as a script."""
    logger = setup_logger(__name__)
    logger.info("Running cleanup utilities...")
    removed = cleanup_mne_cache()
    logger.info(f"Removed {removed} files from MNE cache.")
