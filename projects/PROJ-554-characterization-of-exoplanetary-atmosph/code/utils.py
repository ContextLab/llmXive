"""
Utility functions for the exoplanetary atmosphere characterization pipeline.
Includes logging setup, error handling, and censored data helpers.
"""
import logging
import time
import random
from functools import wraps
from typing import Callable, Type, Optional, Tuple, Any, Union, List
import numpy as np

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DataFetchError(PipelineError):
    """Error raised when data fetching fails."""
    pass

class ParsingError(PipelineError):
    """Error raised when data parsing fails."""
    pass

class RetrievalError(PipelineError):
    """Error raised when retrieval process fails."""
    pass

class CensoredDataError(PipelineError):
    """Error raised when handling censored data fails."""
    pass

class ConfigurationError(PipelineError):
    """Error raised when configuration is invalid."""
    pass

def setup_logging(level: str = 'INFO', log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure logging for the pipeline.
    Sets up console and optionally file handlers.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers
    logger.handlers = []

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def retry_on_failure(max_retries: int = 3, delay: float = 1.0, exceptions: Tuple[Type[Exception], ...] = (Exception,)):
    """
    Decorator to retry a function on failure.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    if retries == max_retries:
                        raise
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Attempt {retries} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

def safe_execute(func: Callable, default: Any = None, exceptions: Tuple[Type[Exception], ...] = (Exception,)) -> Callable:
    """
    Decorator to safely execute a function, returning a default value on exception.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Function {func.__name__} failed with {e}. Returning default.")
            return default
    return wrapper

def is_censored_value(value: Optional[float], threshold: Optional[float] = None) -> bool:
    """
    Check if a value is considered censored (e.g., an upper limit).
    If threshold is provided, checks if value is below threshold.
    """
    if value is None:
        return True
    if threshold is not None and value < threshold:
        return True
    return False

def create_censored_series(data: List[Optional[float]], is_censored: List[bool]) -> pd.Series:
    """
    Create a pandas Series with censored data handling.
    Requires pandas import.
    """
    import pandas as pd
    return pd.Series(data)

def calculate_censored_mean(data: List[float], is_censored: List[bool]) -> float:
    """
    Calculate a mean for censored data (simplified approach).
    In a full implementation, this would use Kaplan-Meier or similar.
    """
    # Simple placeholder: filter out censored values for mean calculation
    uncensored_values = [v for v, c in zip(data, is_censored) if not c]
    if not uncensored_values:
        return np.nan
    return np.mean(uncensored_values)

def handle_non_convergent_retrieval(retrieval_result: Dict[str, Any], fallback_value: float = -10.0) -> Dict[str, Any]:
    """
    Handle cases where retrieval did not converge.
    Sets values to fallback and flags as upper limit.
    """
    retrieval_result['converged'] = False
    retrieval_result['water_mixing_ratio'] = fallback_value
    retrieval_result['is_upper_limit'] = True
    return retrieval_result