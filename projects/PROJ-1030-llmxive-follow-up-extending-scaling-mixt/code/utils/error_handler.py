import logging
import time
from typing import Callable, Type, TypeVar, Optional, List
from functools import wraps
from utils.logging_config import get_logger, fail_loudly

T = TypeVar('T')

class DataFetchError(Exception):
    """Raised when data fetching fails after all retry attempts."""
    pass

class ConfigError(Exception):
    """Raised when configuration is missing or invalid."""
    pass

class PhysicsSimError(Exception):
    """Raised when physics simulation fails."""
    pass

def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: Optional[List[Type[Exception]]] = None,
    logger: Optional[logging.Logger] = None
) -> Callable[..., T]:
    """
    Decorator to retry a function with exponential backoff.
    
    This implements the "FAIL LOUDLY" pattern:
    - Retries transient errors with exponential backoff
    - Fails loudly (raises exception) if all retries are exhausted
    - Never falls back to synthetic data
    
    Args:
        func: Function to decorate
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        backoff_factor: Multiplier for delay after each retry
        retryable_exceptions: List of exception types to retry on (default: all)
        logger: Logger instance (uses default if None)
        
    Returns:
        Decorated function
    """
    if retryable_exceptions is None:
        retryable_exceptions = [Exception]
    
    logger = logger or get_logger(func.__name__)
    
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        delay = initial_delay
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except tuple(retryable_exceptions) as e:
                last_exception = e
                if attempt == max_retries:
                    # All retries exhausted - FAIL LOUDLY
                    error_msg = (
                        f"Data fetch failed after {max_retries} retry attempts. "
                        f"Last error: {str(e)}. "
                        f"FAILO LOUDLY: No synthetic fallback available."
                    )
                    fail_loudly(logger, error_msg, e)
                
                # Log retry attempt
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed: {str(e)}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                time.sleep(delay)
                delay = min(delay * backoff_factor, max_delay)
        
        # Should never reach here, but just in case
        fail_loudly(logger, "Unexpected exit from retry loop", last_exception)
    
    return wrapper

def validate_config(config: dict, required_keys: List[str]) -> None:
    """
    Validate that a configuration dictionary contains all required keys.
    
    Args:
        config: Configuration dictionary to validate
        required_keys: List of required key names
        
    Raises:
        ConfigError: If any required key is missing or has invalid value
    """
    logger = get_logger("config_validator")
    missing_keys = [key for key in required_keys if key not in config or config[key] is None]
    
    if missing_keys:
        error_msg = f"Configuration missing required keys: {', '.join(missing_keys)}"
        fail_loudly(logger, error_msg, ConfigError(error_msg))

def handle_simulation_failure(
    logger: logging.Logger, 
    message: str, 
    exception: Optional[Exception] = None
) -> None:
    """
    Handle physics simulation failures by logging and exiting.
    
    This ensures simulation errors are not silently ignored.
    
    Args:
        logger: Logger instance
        message: Error message
        exception: Optional exception instance
    """
    fail_loudly(logger, f"Physics simulation failed: {message}", exception, error_code=2)
