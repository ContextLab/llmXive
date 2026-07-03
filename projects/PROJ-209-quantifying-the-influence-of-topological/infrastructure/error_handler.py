"""
Error Handling Infrastructure with Exponential Backoff.
Provides retry logic for API calls.
"""
import time
import random
from typing import Callable, Any, Optional, Tuple, Type
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class APIRetryError(Exception):
    """Custom exception for API retry failures."""
    pass

class RateLimitAwareRetry(Exception):
    """Exception indicating rate limit was hit."""
    pass

def is_rate_limit_error(exception: Exception) -> bool:
    """Check if an exception indicates a rate limit error."""
    # Heuristic check for common rate limit indicators
    msg = str(exception).lower()
    return '429' in msg or 'rate limit' in msg or 'too many requests' in msg

def exponential_backoff_retry(
    func: Callable,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0
) -> Callable:
    """
    Decorator to retry a function with exponential backoff.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        delay = base_delay
        last_exception = None

        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if is_rate_limit_error(e) or attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {delay:.2f}s...")
                    time.sleep(delay + random.uniform(0, 0.1 * delay)) # Jitter
                    delay = min(delay * backoff_factor, max_delay)
                else:
                    logger.error(f"Failed after {max_retries} attempts: {e}")
                    raise APIRetryError(f"Max retries exceeded for {func.__name__}") from e
        
        raise APIRetryError("Unexpected retry loop exit")

    return wrapper

def retry_with_backoff(
    func: Callable,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0
) -> Callable:
    """
    Functional wrapper for retrying logic without decorators, useful for one-off calls.
    """
    delay = base_delay
    last_exception = None

    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                logger.warning(f"Retry {attempt + 1}/{max_retries} failed: {e}. Waiting {delay}s.")
                time.sleep(delay)
                delay = min(delay * 2, max_delay)
            else:
                logger.error(f"Function {func.__name__} failed after retries.")
                raise
    raise last_exception
