"""
Cleanup and refactoring utilities for the EEG analysis pipeline.

This module consolidates common utility functions used across the pipeline
to reduce code duplication and improve maintainability.
"""
import os
import logging
import time
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, TypeVar, Union
import numpy as np
import mne
import psutil

from config_loader import get_project_root, get_config, ensure_directory

# Type alias for functions that take no arguments and return nothing
VoidFunc = Callable[[], None]
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

    # Avoid adding handlers multiple times if called repeatedly
    if not logger.handlers:
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler
        if log_file:
            ensure_directory(Path(log_file).parent)
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
    if arr is None:
        raise ValueError("Array cannot be None")

    if not isinstance(arr, np.ndarray):
        raise TypeError(f"Expected numpy.ndarray, got {type(arr)}")

    if arr.ndim < min_dims or arr.ndim > max_dims:
        raise ValueError(
            f"Array has {arr.ndim} dimensions, expected between {min_dims} and {max_dims}"
        )

    if expected_shape is not None:
        if arr.shape != expected_shape:
            raise ValueError(
                f"Array shape {arr.shape} does not match expected {expected_shape}"
            )

    return True

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Perform safe division, returning a default value if division by zero occurs.

    Args:
        numerator: The numerator.
        denominator: The denominator.
        default: Value to return if denominator is zero.

    Returns:
        The result of division or the default value.
    """
    if denominator == 0:
        return default
    return numerator / denominator

def cleanup_mne_cache(cache_dir: Optional[str] = None) -> int:
    """
    Clean up MNE-Python cache directories to free disk space.

    Args:
        cache_dir: Optional specific cache directory to clean.
                   If None, uses MNE's default cache location.

    Returns:
        Number of files removed.
    """
    if cache_dir is None:
        # Default MNE cache location
        home = Path.home()
        cache_dir = str(home / ".mne" / "cache")

    cache_path = Path(cache_dir)
    if not cache_path.exists():
        return 0

    removed_count = 0
    for item in cache_path.rglob("*"):
        if item.is_file():
            try:
                item.unlink()
                removed_count += 1
            except OSError as e:
                logging.warning(f"Could not remove {item}: {e}")

    # Try to remove empty directories
    try:
        for dirpath, dirnames, filenames in os.walk(cache_path, topdown=False):
            if not os.listdir(dirpath):
                os.rmdir(dirpath)
    except OSError:
        pass

    return removed_count

def log_execution_time(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to log the execution time of a function.

    Args:
        func: The function to wrap.

    Returns:
        The wrapped function.
    """
    def wrapper(*args, **kwargs) -> T:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        logging.info(
            f"Function '{func.__name__}' executed in {duration:.2f} seconds"
        )
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
    required_keys = [
        'filter', 'epoch', 'ica', 'channels'
    ]

    for key in required_keys:
        if key not in config:
            raise ValueError(f"Configuration missing required key: {key}")

    # Validate filter settings
    if 'filter' in config:
        f = config['filter']
        if not isinstance(f, dict):
            raise ValueError("Filter config must be a dictionary")
        if 'lowcut' not in f or 'highcut' not in f:
            raise ValueError("Filter config must contain 'lowcut' and 'highcut'")
        if f['lowcut'] >= f['highcut']:
            raise ValueError("Filter lowcut must be less than highcut")

    # Validate epoch settings
    if 'epoch' in config:
        e = config['epoch']
        if not isinstance(e, dict):
            raise ValueError("Epoch config must be a dictionary")
        if 'tmin' not in e or 'tmax' not in e:
            raise ValueError("Epoch config must contain 'tmin' and 'tmax'")

    # Validate ICA settings
    if 'ica' in config:
        i = config['ica']
        if not isinstance(i, dict):
            raise ValueError("ICA config must be a dictionary")
        if 'n_components' in i:
            if not isinstance(i['n_components'], (int, float)) or i['n_components'] <= 0:
                raise ValueError("ICA n_components must be a positive number")

    return True

def find_files_by_extension(directory: Union[str, Path], extension: str) -> List[Path]:
    """
    Recursively find all files with a given extension in a directory.

    Args:
        directory: The directory to search.
        extension: The file extension (e.g., '.fif', '.csv').

    Returns:
        List of Path objects for matching files.
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        logging.warning(f"Directory does not exist: {dir_path}")
        return []

    return list(dir_path.rglob(f"*{extension}"))

def get_memory_usage_gb() -> float:
    """
    Get current memory usage in GB.

    Returns:
        Current memory usage in gigabytes.
    """
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss / (1024 ** 3)

def main() -> None:
    """
    Main entry point for cleanup utilities when run as a script.
    Demonstrates utility functions.
    """
    logger = setup_logger(__name__)
    logger.info("Cleanup utilities module loaded successfully")

    # Example usage
    project_root = get_project_root()
    logger.info(f"Project root: {project_root}")

    # Clean MNE cache
    removed = cleanup_mne_cache()
    logger.info(f"Removed {removed} cached files")

    # Validate a sample config
    sample_config = {
        'filter': {'lowcut': 1.0, 'highcut': 30.0},
        'epoch': {'tmin': -0.2, 'tmax': 0.5},
        'ica': {'n_components': 0.95},
        'channels': ['Fz', 'Cz', 'Pz']
    }

    try:
        validate_pipeline_config(sample_config)
        logger.info("Sample configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")

    logger.info("Cleanup utilities demo completed")

if __name__ == "__main__":
    main()
