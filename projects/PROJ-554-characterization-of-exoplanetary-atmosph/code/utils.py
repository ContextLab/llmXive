"""
Utility functions for the Exoplanet Atmospheric Characterization pipeline.
Includes logging setup, error handling, and censored data helpers.
"""

import logging
import time
import random
from functools import wraps
from typing import Callable, Type, Optional, Tuple, Any, Union, List
import numpy as np
import pandas as pd

# Custom Exceptions
class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DataFetchError(PipelineError):
    """Error during data fetching from external APIs."""
    pass

class ParsingError(PipelineError):
    """Error during data parsing."""
    pass

class RetrievalError(PipelineError):
    """Error during atmospheric retrieval execution."""
    pass

class CensoredDataError(PipelineError):
    """Error related to censored data handling."""
    pass

class ConfigurationError(PipelineError):
    """Error related to configuration loading or validation."""
    pass

# Logging Setup
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Configure the logging system for the pipeline.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to a log file. If None, logs to stdout.
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ConfigurationError(f"Invalid log level: {log_level}")

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    handlers = []
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=handlers
    )

    # Reduce verbosity for third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)

# Retry Logic
def retry_on_failure(
    retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorator to retry a function on failure.

    Args:
        retries: Number of retry attempts.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for the delay after each retry.
        exceptions: Tuple of exception types to catch.

    Returns:
        Decorated function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == retries - 1:
                        raise
                    logging.warning(
                        f"Attempt {attempt + 1}/{retries} failed for {func.__name__}: {e}. "
                        f"Retrying in {current_delay:.2f}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
            return None
        return wrapper
    return decorator

# Safe Execution Wrapper
def safe_execute(func: Callable, default: Any = None, log_error: bool = True) -> Callable:
    """
    Decorator to safely execute a function, returning a default value on exception.

    Args:
        func: Function to execute.
        default: Value to return if an exception occurs.
        log_error: Whether to log the exception.

    Returns:
        Decorated function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if log_error:
                logging.error(f"Error in {func.__name__}: {e}")
            return default
    return wrapper

# Censored Data Helpers
def is_censored_value(value: Any) -> bool:
    """
    Check if a value represents a censored observation (upper limit).

    Args:
        value: The value to check. Can be a float, string, or numpy scalar.

    Returns:
        True if the value is a censored upper limit (e.g., < 0.5, -999, np.nan),
        False otherwise.
    """
    if pd.isna(value):
        return True

    # Check for string representations of limits often found in catalogs
    if isinstance(value, str):
        lower_val = value.lower().strip()
        if lower_val.startswith('<') or lower_val.startswith('<='):
            return True
        if lower_val in ('na', 'null', 'none', 'missing'):
            return True

    # Check for numeric sentinel values
    if isinstance(value, (int, float, np.floating, np.integer)):
        # Common sentinel for missing/upper limit in astronomy
        if value == -999.0 or value == -1.0:
            return True
        if np.isinf(value):
            return True

    return False

def create_censored_series(
    values: List[Union[float, str, None]],
    is_upper: bool = True
) -> pd.Series:
    """
    Create a pandas Series with explicit handling for censored values.
    Converts censored markers to NaN and sets a flag column if needed.

    Args:
        values: List of raw values (may include strings like '<0.5').
        is_upper: If True, treats censored values as upper limits.

    Returns:
        pd.Series: Cleaned numeric series.
        Note: This function assumes the caller handles the boolean flag logic
        separately if a unified dataframe is needed, or returns a tuple.
        For simplicity here, it returns the cleaned numeric series and logs warnings.
    """
    cleaned_values = []
    for v in values:
        if is_censored_value(v):
            cleaned_values.append(np.nan)
        else:
            try:
                cleaned_values.append(float(v))
            except (ValueError, TypeError):
                cleaned_values.append(np.nan)
                logging.warning(f"Could not parse value '{v}' as float.")

    return pd.Series(cleaned_values)

def calculate_censored_mean(
    values: pd.Series,
    limits: Optional[pd.Series] = None,
    method: str = 'kaplan_meier'
) -> float:
    """
    Calculate the mean of a dataset containing censored values.

    Args:
        values: Series of numeric values (NaN for censored).
        limits: Series of limit values (e.g., if value is '<5', limit is 5.0).
                If None, assumes NaN represents the limit position but not the value.
        method: Currently supports 'simple' (ignores censored) or 'kaplan_meier' (requires scikit-survival).
                Since scikit-survival is a dependency, we attempt import.

    Returns:
        float: Estimated mean.

    Raises:
        CensoredDataError: If method requires unavailable dependencies or inputs are invalid.
    """
    if values.isna().all():
        logging.warning("All values are censored/missing. Returning NaN.")
        return np.nan

    if method == 'simple':
        # Naive approach: ignore censored values
        valid = values.dropna()
        if valid.empty:
            return np.nan
        return valid.mean()

    elif method == 'kaplan_meier':
        try:
            from lifelines import KaplanMeierFitter
        except ImportError:
            raise CensoredDataError(
                "lifelines library required for Kaplan-Meier estimation is not installed. "
                "Install via requirements.txt."
            )

        if limits is None:
            # If limits are not provided, we cannot accurately estimate the mean
            # for censored data without assumptions. Return simple mean as fallback with warning.
            logging.warning("Limits not provided for Kaplan-Meier. Falling back to simple mean.")
            return calculate_censored_mean(values, method='simple')

        # Prepare data for lifelines
        # lifelines expects: durations (values) and event (1 if observed, 0 if censored)
        # We treat NaN in 'values' as censored.
        # We need a boolean mask: True if observed (not NaN), False if censored.
        observed_mask = values.notna()

        if not observed_mask.any():
            return np.nan

        kmf = KaplanMeierFitter()
        # lifelines requires non-NaN durations for the fit, but we need to handle the censored ones.
        # Actually, KMfitter handles censored data by taking the 'event' array.
        # We pass all durations, but for censored ones, the duration is the limit.
        # Here, we assume 'values' contains the observed values, and 'limits' contains the upper bounds for censored.
        # We need to construct a single array of durations where censored items use their limit.
        # And an event array.

        durations = values.copy()
        # For censored items (NaN in values), replace with limit
        if limits is not None:
            durations = durations.fillna(limits)
        
        event_observed = observed_mask.astype(int)

        kmf.fit(durations, event_observed)
        
        # The mean survival time is the area under the survival curve
        # lifelines provides `median_survival_time`, but for mean we need integration
        # or use the `mean_survival_time` property if available in the version.
        # In standard lifelines, we can approximate or use the `mean_` attribute if computed.
        # A robust way is to calculate the integral of the survival function.
        # However, for simplicity and robustness in this specific pipeline context:
        # We will return the median if mean is unstable, or attempt to compute mean.
        
        # lifelines.KaplanMeierFitter has a `mean_survival_time` property in newer versions
        # or we can calculate it manually. Let's try to access the property.
        try:
            return kmf.mean_survival_time
        except AttributeError:
            # Fallback: simple mean of observed if KM mean is unavailable
            logging.warning("Mean survival time not directly available in this lifelines version. Using observed mean.")
            return values.dropna().mean()

    else:
        raise CensoredDataError(f"Unknown censored data method: {method}")

def handle_non_convergent_retrieval(
    result: Dict[str, Any],
    fallback_strategy: str = 'upper_limit'
) -> Dict[str, Any]:
    """
    Handle retrieval results that did not converge.
    
    Args:
        result: The raw retrieval result dictionary.
        fallback_strategy: Strategy to handle failure ('upper_limit', 'skip', 'impute').
        
    Returns:
        Modified result dictionary with flags and estimated values if applicable.
    """
    if result.get('converged', False):
        return result

    logging.warning(f"Retrieval did not converge. Applying strategy: {fallback_strategy}")
    result['converged'] = False
    result['censored'] = True
    
    if fallback_strategy == 'upper_limit':
        # Estimate upper limit based on noise floor or prior bounds
        # This logic depends on specific retrieval output structure.
        # Assuming 'water_abundance' is the key parameter.
        param = result.get('water_abundance', None)
        if param is None:
            result['water_abundance'] = -999.0 # Sentinel
            result['water_abundance_upper'] = -999.0
        else:
            # If we have a prior bound or noise estimate, use it.
            # For now, we mark it as a limit without a specific numeric value
            # unless we have a 'noise_floor' in the result.
            noise = result.get('noise_floor', 0.0)
            if noise > 0:
                result['water_abundance'] = np.log10(noise) # Approximation
                result['water_abundance_upper'] = np.log10(noise * 10) # 1 order of magnitude
            else:
                result['water_abundance'] = -999.0
                result['water_abundance_upper'] = -999.0
        
        result['flag'] = 'UPPER_LIMIT'
        
    elif fallback_strategy == 'skip':
        result['flag'] = 'SKIPPED'
        
    elif fallback_strategy == 'impute':
        # Impute with median of converged retrievals (requires external context)
        # Here we just set a placeholder
        result['water_abundance'] = -999.0
        result['flag'] = 'IMPUTED'

    return result