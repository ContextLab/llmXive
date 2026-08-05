import logging
import time
import random
from functools import wraps
from typing import Callable, Type, Optional, Tuple, Any, Union, List
import numpy as np

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

def setup_logging(level=logging.INFO):
    """Configure logging for the pipeline."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('pipeline.log')
        ]
    )

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
                        logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                        raise
                    logger.warning(f"Function {func.__name__} failed, retrying in {delay}s... ({retries}/{max_retries})")
                    time.sleep(delay * random.uniform(0.5, 1.5))
        return wrapper
    return decorator

def safe_execute(func: Callable, default: Any = None, logger_name: str = __name__) -> Callable:
    """
    Decorator to safely execute a function, returning a default value on exception.
    """
    log = logging.getLogger(logger_name)
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log.error(f"Error in {func.__name__}: {e}")
            return default
    return wrapper

def is_censored_value(value: Any) -> bool:
    """Check if a value represents a censored data point (e.g., upper limit)."""
    if isinstance(value, (int, float)):
        return np.isnan(value) or value == -999.0 # Common sentinel for missing/upper limit
    return False

def create_censored_series(data: List[Dict[str, Any]], value_key: str, is_censored_key: str) -> pd.Series:
    """
    Create a pandas Series from a list of dictionaries, handling censored values.
    Requires pandas to be imported.
    """
    try:
        import pandas as pd
        values = []
        for item in data:
            val = item.get(value_key)
            if item.get(is_censored_key, False):
                # Mark as censored (e.g., use NaN or a specific marker)
                values.append(np.nan) 
            else:
                values.append(val)
        return pd.Series(values)
    except ImportError:
        logger.error("pandas not installed, cannot create censored series")
        raise

def calculate_censored_mean(data: List[float], censored_flags: List[bool]) -> Optional[float]:
    """
    Calculate the mean of a dataset, treating censored values appropriately.
    For upper limits, a simple mean is not statistically valid; this is a placeholder.
    In practice, one would use survival analysis methods (e.g., Kaplan-Meier).
    """
    if not data or not censored_flags:
        return None
    
    # Simple implementation: ignore censored values for now
    # A proper implementation would use scikit-survival or lifelines
    valid_values = [v for v, c in zip(data, censored_flags) if not c]
    if not valid_values:
        return None
    return np.mean(valid_values)

def handle_non_convergent_retrieval(spectrum_id: str, error: Exception, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Handle non-convergent retrievals by attempting to derive an upper limit.
    Returns a dictionary with upper limit data or None if derivation also fails.
    """
    logger.warning(f"Retrieval for {spectrum_id} did not converge: {error}. Attempting upper limit derivation.")
    try:
        # Placeholder for actual upper limit derivation logic
        # This would typically involve analyzing the noise floor of the spectrum
        noise_estimate = 1e-3 # Example noise estimate
        upper_limit_value = 3.0 * noise_estimate
        
        return {
            "log10_water_mixing_ratio": np.log10(upper_limit_value),
            "is_upper_limit": True,
            "censorship_status": "UPPER_LIMIT",
            "error_message": f"Non-convergent, upper limit derived: {error}"
        }
    except Exception as fallback_error:
        logger.error(f"Failed to derive upper limit for {spectrum_id} after non-convergence: {fallback_error}")
        return None