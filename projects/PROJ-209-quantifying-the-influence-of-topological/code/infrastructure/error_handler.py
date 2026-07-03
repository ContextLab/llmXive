import time
import random
from typing import Callable, Any, Optional, Type
from functools import wraps
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

class APIRetryError(Exception):
    """Exception raised when all retry attempts fail."""
    pass

def is_rate_limit_error(exception: Exception) -> bool:
    """
    Determine if an exception indicates a rate limit or transient server error.
    Checks for common HTTP status codes (429, 503, 502, 504) or specific
    exception types if available.
    """
    # Common HTTP status codes for rate limits and server errors
    rate_limit_codes = {429, 503, 502, 504}
    
    # Check if the exception has a status_code attribute (e.g., requests.HTTPError)
    if hasattr(exception, 'status_code'):
        return int(exception.status_code) in rate_limit_codes
    
    # Check exception message for common keywords
    msg = str(exception).lower()
    if any(keyword in msg for keyword in ['rate limit', '429', '503', 'too many requests', 'service unavailable']):
        return True
        
    return False

def exponential_backoff_retry(
    func: Callable,
    max_retries: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True
) -> Callable:
    """
    Decorator to apply exponential backoff retry logic to a function.
    
    Args:
        func: The function to wrap.
        max_retries: Maximum number of retry attempts.
        initial_delay: Initial delay in seconds before the first retry.
        max_delay: Maximum delay in seconds between retries.
        backoff_factor: Multiplier for the delay (e.g., 2.0 means delay doubles each time).
        jitter: If True, adds random jitter to the delay to prevent thundering herd.
        
    Returns:
        The wrapped function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        delay = initial_delay
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # If it's the last attempt, raise immediately
                if attempt == max_retries:
                    logger.error(f"Failed after {max_retries} retries: {e}")
                    raise APIRetryError(f"Function {func.__name__} failed after {max_retries} retries: {e}") from e
                
                # Only retry on rate limit or transient errors
                if not is_rate_limit_error(e):
                    logger.warning(f"Non-retryable error ({type(e).__name__}): {e}. Raising immediately.")
                    raise
                
                # Calculate delay with jitter
                current_delay = min(delay, max_delay)
                if jitter:
                    current_delay = current_delay * (0.5 + random.random())
                
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                    f"Retrying in {current_delay:.2f}s..."
                )
                
                time.sleep(current_delay)
                delay *= backoff_factor
        
        # Should not reach here, but just in case
        raise APIRetryError(f"Function {func.__name__} failed unexpectedly.")
    
    return wrapper

def retry_with_backoff(
    func: Callable,
    max_retries: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True
) -> Callable:
    """
    Alias for exponential_backoff_retry for clarity in different contexts.
    """
    return exponential_backoff_retry(
        func,
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
        jitter=jitter
    )

class RateLimitAwareRetry:
    """
    Context manager or class-based interface for retrying operations with exponential backoff.
    Useful when more control is needed than a simple decorator provides.
    """
    def __init__(
        self,
        max_retries: int = 5,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.logger = logging.getLogger(self.__class__.__name__)

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = self.initial_delay
            last_exception = None
            
            for attempt in range(self.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == self.max_retries:
                        self.logger.error(f"Failed after {self.max_retries} retries: {e}")
                        raise APIRetryError(f"Function {func.__name__} failed after {self.max_retries} retries: {e}") from e
                    
                    if not is_rate_limit_error(e):
                        self.logger.warning(f"Non-retryable error ({type(e).__name__}): {e}. Raising immediately.")
                        raise
                    
                    current_delay = min(delay, self.max_delay)
                    if self.jitter:
                        current_delay = current_delay * (0.5 + random.random())
                    
                    self.logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries} failed for {func.__name__}: {e}. "
                        f"Retrying in {current_delay:.2f}s..."
                    )
                    
                    time.sleep(current_delay)
                    delay *= self.backoff_factor
            
            raise APIRetryError(f"Function {func.__name__} failed unexpectedly.")
        
        return wrapper