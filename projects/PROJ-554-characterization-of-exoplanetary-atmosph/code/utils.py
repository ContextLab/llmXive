"""
Utility functions for the exoplanet atmosphere characterization pipeline.
"""

import logging
import time
import random
from functools import wraps
from typing import Callable, Type, Optional, Tuple, Any, Union, List
import numpy as np
from pathlib import Path


class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass


class DataFetchError(PipelineError):
    """Exception raised when data fetching fails."""
    pass


class ParsingError(PipelineError):
    """Exception raised when data parsing fails."""
    pass


class RetrievalError(PipelineError):
    """Exception raised when retrieval fails."""
    pass


class CensoredDataError(PipelineError):
    """Exception raised when handling censored data fails."""
    pass


class ConfigurationError(PipelineError):
    """Exception raised when configuration fails."""
    pass


def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging for the pipeline.

    Args:
        log_file: Optional path to log file. If None, logs to console only.
        level: Logging level.

    Returns:
        Configured logger.
    """
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(console_handler)
    
    # File handler if log_file is provided
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(file_handler)
    
    return logger


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions: Tuple[Type[Exception], ...] = (Exception,)):
    """
    Decorator to retry a function on failure.

    Args:
        max_retries: Maximum number of retries.
        delay: Initial delay between retries.
        backoff: Multiplier for delay between retries.
        exceptions: Tuple of exceptions to catch.

    Returns:
        Decorated function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger = logging.getLogger(func.__module__)
                        logger.warning(f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. Retrying in {current_delay}s...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}: {e}")
                        raise
            
            # Should not reach here, but just in case
            raise last_exception
        return wrapper
    return decorator


def is_censored_value(value: Any) -> bool:
    """
    Check if a value represents a censored observation (upper limit).

    Args:
        value: Value to check.

    Returns:
        True if the value is censored, False otherwise.
    """
    if pd.isna(value):
        return True
    if isinstance(value, str) and value.lower() in ['upper', 'limit', 'censored', '<', '>']:
        return True
    return False


def create_censored_series(series: pd.Series, threshold: Optional[float] = None) -> pd.Series:
    """
    Create a censored series from a regular series.

    Args:
        series: Input series.
        threshold: Optional threshold for censoring.

    Returns:
        Censored series.
    """
    if threshold is not None:
        return series.where(series > threshold, np.nan)
    return series


def calculate_censored_mean(series: pd.Series) -> float:
    """
    Calculate mean for censored data (treating NaN as lower bound).

    Args:
        series: Censored series.

    Returns:
        Mean of non-censored values.
    """
    return series.dropna().mean()


def handle_non_convergent_retrieval(error: Exception, default_value: Optional[float] = None) -> Dict[str, Any]:
    """
    Handle non-convergent retrieval by returning a default value or upper limit.

    Args:
        error: The exception that occurred.
        default_value: Optional default value to return.

    Returns:
        Dictionary with result and status.
    """
    logger = logging.getLogger(__name__)
    logger.warning(f"Non-convergent retrieval: {error}")
    
    return {
        'water_mixing_ratio': default_value,
        'uncertainty': None,
        'is_upper_limit': True,
        'convergence_status': 'failed',
        'error_message': str(error)
    }


def safe_execute(func: Callable, *args, default: Any = None, **kwargs) -> Any:
    """
    Safely execute a function, returning default on error.

    Args:
        func: Function to execute.
        *args: Positional arguments.
        default: Default value to return on error.
        **kwargs: Keyword arguments.

    Returns:
        Function result or default value.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"Error executing {func.__name__}: {e}")
        return default