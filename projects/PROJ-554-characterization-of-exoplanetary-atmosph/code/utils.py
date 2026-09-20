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
    """Error handling censored data."""
    pass

class ConfigurationError(PipelineError):
    """Error in configuration."""
    pass

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Configure logging for the pipeline."""
    logger = logging.getLogger("llmXive")
    logger.setLevel(level)

    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Decorator to retry a function on failure."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logging.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff

            raise last_exception
        return wrapper
    return decorator

def is_censored_value(value: Optional[float]) -> bool:
    """Check if a value is a censored upper limit."""
    return value is None or (isinstance(value, float) and np.isnan(value))

def create_censored_series(data: List[Optional[float]], is_censored: List[bool]) -> pd.Series:
    """Create a pandas Series with censored data markers.

    Args:
        data: List of values, where None represents a censored upper limit.
        is_censored: List of booleans indicating if the corresponding value is censored.

    Returns:
        A pandas Series where censored values are marked with a specific sentinel (e.g., -999).
    """
    if len(data) != len(is_censored):
        raise ValueError("Data and is_censored lists must have the same length.")

    processed_data = []
    for val, cens in zip(data, is_censored):
        if cens or is_censored_value(val):
            processed_data.append(np.nan)
        else:
            processed_data.append(val)

    return pd.Series(processed_data)

def calculate_censored_mean(values: List[Optional[float]], is_censored: List[bool]) -> float:
    """Calculate the mean of non-censored values.

    Args:
        values: List of values.
        is_censored: List of booleans indicating censored status.

    Returns:
        Mean of non-censored values.
    """
    non_censored = [v for v, c in zip(values, is_censored) if v is not None and not c]
    if not non_censored:
        return np.nan
    return np.mean(non_censored)

def handle_non_convergent_retrieval(planet_name: str, error: Exception, logger: logging.Logger) -> dict:
    """Handle a non-convergent retrieval by returning an upper limit placeholder.

    Args:
        planet_name: Name of the planet.
        error: The exception that occurred.
        logger: Logger instance.

    Returns:
        A dictionary representing an upper limit result.
    """
    logger.error(f"Retrieval failed for {planet_name}: {error}")
    return {
        "planet_name": planet_name,
        "water_mixing_ratio": np.nan,
        "uncertainty": np.nan,
        "is_upper_limit": True,
        "convergence_status": "failed",
        "error_message": str(error)
    }

def safe_execute(func: Callable, *args, default: Any = None, logger: Optional[logging.Logger] = None) -> Any:
    """Safely execute a function and return a default value on failure.

    Args:
        func: Function to execute.
        *args: Arguments to pass to the function.
        default: Default value to return on failure.
        logger: Optional logger to log the error.

    Returns:
        Result of func or default.
    """
    try:
        return func(*args)
    except Exception as e:
        if logger:
            logger.warning(f"Function {func.__name__} failed: {e}")
        return default
