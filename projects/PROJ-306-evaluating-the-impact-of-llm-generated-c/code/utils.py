import time
import random
from typing import Callable, Any, TypeVar, Optional
import logging

T = TypeVar('T')

def calculate_backoff_delay(retry_count: int, base_delay: float = 1.0, max_delay: float = 60.0, jitter: float = 0.2) -> float:
    """
    Calculate exponential backoff delay with jitter.
    
    Args:
        retry_count: Current retry attempt (0-indexed)
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap
        jitter: Jitter factor (0.0 to 1.0) for randomness
    
    Returns:
        Delay in seconds
    """
    # Exponential backoff: base_delay * 2^retry_count
    delay = min(base_delay * (2 ** retry_count), max_delay)
    
    # Add jitter to prevent thundering herd
    jitter_amount = delay * jitter * random.random()
    return delay + jitter_amount

def is_rate_limit_error(exception: Exception) -> bool:
    """
    Check if an exception is a rate limit error.
    
    Args:
        exception: The exception to check
    
    Returns:
        True if it's a rate limit error, False otherwise
    """
    error_str = str(exception).lower()
    rate_limit_keywords = [
        'rate limit', 'too many requests', '429', 'quota exceeded',
        'throttled', 'slow down', 'limit reached'
    ]
    return any(keyword in error_str for keyword in rate_limit_keywords)

def retry_with_exponential_backoff(
    func: Callable[..., T],
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    logger: Optional[logging.Logger] = None
) -> Callable[..., T]:
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        func: Function to wrap
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap
        logger: Optional logger for progress updates
    
    Returns:
        Wrapped function
    """
    def wrapper(*args, **kwargs) -> T:
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                # Check if it's a rate limit error
                if is_rate_limit_error(e):
                    if attempt < max_retries:
                        delay = calculate_backoff_delay(attempt, base_delay, max_delay)
                        msg = f"Rate limit hit. Retrying in {delay:.2f}s (attempt {attempt + 1}/{max_retries})"
                        if logger:
                            logger.warning(msg)
                        else:
                            print(f"WARNING: {msg}")
                        time.sleep(delay)
                    else:
                        msg = f"Max retries ({max_retries}) exceeded for rate limit error"
                        if logger:
                            logger.error(msg)
                        raise
                else:
                    # Non-rate-limit error, don't retry
                    if logger:
                        logger.error(f"Non-retryable error: {str(e)}")
                    raise
        
        # Should not reach here, but just in case
        raise last_exception

    wrapper.__name__ = func.__name__
    return wrapper

def safe_call_with_retry(
    func: Callable[..., T],
    args: tuple = (),
    kwargs: Optional[dict] = None,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    logger: Optional[logging.Logger] = None
) -> tuple:
    """
    Safely call a function with retry logic. Returns (success, result/error).
    
    Args:
        func: Function to call
        args: Positional arguments
        kwargs: Keyword arguments
        max_retries: Maximum retries
        base_delay: Initial delay
        max_delay: Max delay cap
        logger: Optional logger
    
    Returns:
        Tuple of (success: bool, result: Any or error: str)
    """
    kwargs = kwargs or {}
    decorated_func = retry_with_exponential_backoff(
        func, max_retries, base_delay, max_delay, logger
    )
    
    try:
        result = decorated_func(*args, **kwargs)
        return (True, result)
    except Exception as e:
        return (False, str(e))
