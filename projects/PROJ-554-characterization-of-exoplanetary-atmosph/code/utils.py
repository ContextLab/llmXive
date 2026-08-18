"""
Utility functions for the exoplanet atmospheric analysis pipeline.
Includes custom exceptions, retry logic, and censored data helpers.
"""
import logging
import time
import random
from functools import wraps
from typing import Callable, Type, Optional, Tuple, Any, Union, List
import numpy as np

# Setup logger
logger = logging.getLogger(__name__)

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

def setup_logging(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Sets up logging for a specific module.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler if specified
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.DEBUG)
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
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt}/{max_retries} failed for {func.__name__}: {e}")
                    if attempt < max_retries:
                        time.sleep(delay * (2 ** (attempt - 1)) + random.uniform(0, 1))
            logger.error(f"All {max_retries} attempts failed for {func.__name__}. Last error: {last_exception}")
            raise last_exception
        return wrapper
    return decorator

def safe_execute(func: Callable, default: Any = None, exceptions: Tuple[Type[Exception], ...] = (Exception,)) -> Any:
    """
    Safely executes a function, returning a default value on exception.
    """
    try:
        return func()
    except exceptions as e:
        logger.warning(f"Function {func.__name__} failed: {e}. Returning default.")
        return default

def is_censored_value(value: Union[float, np.floating]) -> bool:
    """
    Checks if a value is a censored value (e.g., upper limit).
    """
    return np.isnan(value) or value == -999.0

def create_censored_series(data: List[Dict[str, Any]], value_key: str, limit_key: str) -> pd.Series:
    """
    Creates a pandas Series handling censored data.
    """
    import pandas as pd
    values = []
    events = [] # 1 for observed, 0 for censored

    for item in data:
        val = item.get(value_key)
        lim = item.get(limit_key)
        
        if is_censored_value(val):
            values.append(lim if lim is not None else 0)
            events.append(0)
        else:
            values.append(val)
            events.append(1)
    
    s = pd.Series(values)
    s.name = value_key
    s.attrs['event'] = pd.Series(events, name='event')
    return s

def calculate_censored_mean(series: pd.Series, event_series: pd.Series) -> float:
    """
    Calculates the mean of a censored dataset (simplified).
    """
    observed = series[event_series == 1]
    if len(observed) == 0:
        return np.nan
    return observed.mean()

def handle_non_convergent_retrieval(planet_name: str, error_msg: str, fallback_func: Optional[Callable] = None, fallback_args: Tuple = ()) -> Dict[str, Any]:
    """
    Handles non-convergent retrievals by logging the failure and attempting a fallback (e.g., upper limit derivation).
    
    Args:
        planet_name: Name of the planet.
        error_msg: The error message from the failed retrieval.
        fallback_func: Optional function to call as a fallback.
        fallback_args: Arguments to pass to the fallback function.
        
    Returns:
        A result dictionary indicating the outcome.
    """
    logger.warning(f"Non-convergent retrieval for {planet_name}: {error_msg}")
    
    result = {
        'planet_name': planet_name,
        'status': 'fallback_attempted',
        'original_error': error_msg,
        'fallback_success': False,
        'fallback_result': None
    }

    if fallback_func:
        try:
            logger.info(f"Attempting fallback for {planet_name}...")
            fallback_result = fallback_func(*fallback_args)
            result['fallback_success'] = True
            result['fallback_result'] = fallback_result
            result['status'] = 'success_via_fallback'
            logger.info(f"Fallback successful for {planet_name}")
        except Exception as e:
            logger.error(f"Fallback failed for {planet_name}: {e}")
            result['fallback_success'] = False
            result['status'] = 'failed'
    else:
        logger.info(f"No fallback function provided for {planet_name}. Proceeding without result.")
        result['status'] = 'proceed_without_result'

    return result
