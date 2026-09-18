import logging
import time
import random
from functools import wraps
from typing import Callable, Type, Optional, Tuple, Any, Union, List
import numpy as np
import pandas as pd

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DataFetchError(PipelineError):
    """Error during data fetching."""
    pass

class ParsingError(PipelineError):
    """Error during data parsing."""
    pass

class RetrievalError(PipelineError):
    """Error during atmospheric retrieval."""
    pass

class CensoredDataError(PipelineError):
    """Error related to censored data handling."""
    pass

class ConfigurationError(PipelineError):
    """Error related to configuration."""
    pass

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging for the pipeline.

    Args:
        log_file: Path to log file. If None, logs to console only.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("exoplanet_pipeline")
    logger.setLevel(level)

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler if specified
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry a function on failure.

    Args:
        max_retries: Maximum number of retry attempts.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for delay after each retry.

    Returns:
        Decorator function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {current_delay}s...")
                    time.sleep(current_delay)
                    current_delay *= backoff
            return None
        return wrapper
    return decorator

def safe_execute(func: Callable, default: Any = None, log_error: bool = True) -> Any:
    """
    Safely execute a function and return a default value on failure.

    Args:
        func: Function to execute.
        default: Default value to return on failure.
        log_error: Whether to log the error.

    Returns:
        Function result or default value.
    """
    try:
        return func()
    except Exception as e:
        if log_error:
            logging.error(f"Error executing {func.__name__}: {e}")
        return default

def is_censored_value(value: Optional[float], threshold: float = -999.0) -> bool:
    """
    Check if a value represents a censored measurement (upper limit).

    Args:
        value: The value to check.
        threshold: Sentinel value indicating censorship (default -999.0).

    Returns:
        True if the value is censored, False otherwise.
    """
    if value is None:
        return True
    return np.isclose(value, threshold)

def create_censored_series(data: List[Optional[float]], is_censored: List[bool]) -> pd.Series:
    """
    Create a pandas Series representing censored data.

    Args:
        data: List of values (None or sentinel for censored).
        is_censored: List of booleans indicating if each value is censored.

    Returns:
        Pandas Series with values, replacing censored entries with np.nan.
    """
    if len(data) != len(is_censored):
        raise ValueError("data and is_censored must have the same length")

    processed_data = []
    for val, censored in zip(data, is_censored):
        if censored or val is None:
            processed_data.append(np.nan)
        else:
            processed_data.append(val)

    return pd.Series(processed_data)

def calculate_censored_mean(data: List[Optional[float]], is_censored: List[bool]) -> Optional[float]:
    """
    Calculate the mean of non-censored values.

    Args:
        data: List of values.
        is_censored: List of booleans indicating censorship.

    Returns:
        Mean of non-censored values, or None if all are censored.
    """
    valid_values = [v for v, c in zip(data, is_censored) if not c and v is not None]
    if not valid_values:
        return None
    return float(np.mean(valid_values))

def handle_non_convergent_retrieval(planet_name: str, error: Exception, logger: Optional[logging.Logger] = None) -> Dict[str, Any]:
    """
    Handle non-convergent retrieval results by creating a fallback record.

    Args:
        planet_name: Name of the planet.
        error: The exception that occurred.
        logger: Logger instance (optional).

    Returns:
        Dictionary representing a fallback retrieval result (upper limit).
    """
    result = {
        "planet_name": planet_name,
        "water_mixing_ratio": np.nan,
        "uncertainty": np.nan,
        "is_upper_limit": True,
        "convergence_status": "failed",
        "error_message": str(error)
    }

    log_msg = f"Retrieval failed for {planet_name}: {error}. Marking as upper limit."
    if logger:
        logger.warning(log_msg)
    else:
        logging.warning(log_msg)

    return result
