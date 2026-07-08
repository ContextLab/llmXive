"""
Rate limit handler for Pushshift API interactions.
Handles 429 responses and integrates with retry_policy.py for exponential backoff.
"""
import time
import logging
from typing import Optional, Callable, Any, Dict
from functools import wraps

from .retry_policy import retry_with_backoff, RetryConfig, calculate_backoff_delay

logger = logging.getLogger(__name__)

# Default configuration for Pushshift rate limiting
PUSHSHIFT_RETRY_CONFIG = RetryConfig(
    max_retries=5,
    base_delay=1.0,  # Start with 1 second
    max_delay=60.0,  # Cap at 60 seconds
    exponential_base=2.0,
    jitter=True
)

class RateLimitError(Exception):
    """Raised when rate limit is exceeded and retries are exhausted."""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after

def extract_retry_after(response: Any) -> Optional[int]:
    """
    Extract Retry-After header from response if available.
    Returns seconds to wait, or None if not present.
    """
    if response is None:
        return None
    
    # Handle requests.Response object
    if hasattr(response, 'headers'):
        retry_header = response.headers.get('Retry-After')
        if retry_header:
            try:
                return int(retry_header)
            except ValueError:
                logger.warning(f"Invalid Retry-After header value: {retry_header}")
    
    # Handle dictionary-like response
    if isinstance(response, dict):
        retry_header = response.get('retry_after') or response.get('Retry-After')
        if retry_header:
            try:
                return int(retry_header)
            except ValueError:
                logger.warning(f"Invalid Retry-After header value: {retry_header}")
    
    return None

def handle_429_response(response: Any, attempt: int, max_retries: int) -> None:
    """
    Handle a 429 rate limit response.
    
    Args:
        response: The HTTP response object
        attempt: Current retry attempt number (0-indexed)
        max_retries: Maximum number of retries allowed
        
    Raises:
        RateLimitError: If max retries exceeded
    """
    if attempt >= max_retries:
        retry_after = extract_retry_after(response)
        raise RateLimitError(
            f"Pushshift API rate limit exceeded after {max_retries} attempts",
            retry_after=retry_after
        )
    
    # Calculate backoff delay
    retry_after_header = extract_retry_after(response)
    
    if retry_after_header is not None:
        # Respect server's Retry-After header
        delay = retry_after_header
        logger.warning(
            f"Rate limited by Pushshift. Server suggests waiting {delay}s. "
            f"Attempt {attempt + 1}/{max_retries}"
        )
    else:
        # Use exponential backoff
        delay = calculate_backoff_delay(
            attempt=attempt,
            base_delay=PUSHSHIFT_RETRY_CONFIG.base_delay,
            max_delay=PUSHSHIFT_RETRY_CONFIG.max_delay,
            exponential_base=PUSHSHIFT_RETRY_CONFIG.exponential_base,
            jitter=PUSHSHIFT_RETRY_CONFIG.jitter
        )
        logger.warning(
            f"Rate limited by Pushshift. Waiting {delay:.2f}s before retry. "
            f"Attempt {attempt + 1}/{max_retries}"
        )
    
    time.sleep(delay)

def rate_limit_handler(
    retry_config: Optional[RetryConfig] = None
) -> Callable:
    """
    Decorator to handle rate limiting for API calls.
    
    Args:
        retry_config: Optional custom retry configuration. Defaults to PUSHSHIFT_RETRY_CONFIG.
        
    Returns:
        Decorated function with rate limit handling
    """
    config = retry_config or PUSHSHIFT_RETRY_CONFIG
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    response = func(*args, **kwargs)
                    
                    # Check if response indicates rate limit
                    if hasattr(response, 'status_code') and response.status_code == 429:
                        handle_429_response(response, attempt, config.max_retries)
                        continue
                    elif isinstance(response, dict) and response.get('status_code') == 429:
                        handle_429_response(response, attempt, config.max_retries)
                        continue
                    
                    return response
                    
                except RateLimitError as e:
                    # This is raised when max retries exceeded
                    logger.error(f"Rate limit handling failed: {e}")
                    raise
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Unexpected error in {func.__name__}: {e}. Attempt {attempt + 1}/{config.max_retries + 1}")
                    
                    # For non-429 errors, use standard retry logic
                    if attempt < config.max_retries:
                        delay = calculate_backoff_delay(
                            attempt=attempt,
                            base_delay=config.base_delay,
                            max_delay=config.max_delay,
                            exponential_base=config.exponential_base,
                            jitter=config.jitter
                        )
                        logger.info(f"Retrying after {delay:.2f}s due to error: {e}")
                        time.sleep(delay)
                    continue
            
            # All retries exhausted
            if last_exception:
                raise last_exception
            raise RateLimitError(f"Failed to complete {func.__name__} after {config.max_retries + 1} attempts")
        
        return wrapper
    
    return decorator

def is_rate_limited(response: Any) -> bool:
    """
    Check if a response indicates rate limiting.
    
    Args:
        response: The HTTP response object or dictionary
        
    Returns:
        True if rate limited, False otherwise
    """
    if response is None:
        return False
    
    if hasattr(response, 'status_code'):
        return response.status_code == 429
    
    if isinstance(response, dict):
        return response.get('status_code') == 429 or response.get('error') == 'rate_limit_exceeded'
    
    return False

@retry_with_backoff(retry_config=PUSHSHIFT_RETRY_CONFIG)
def safe_api_call(func: Callable, *args, **kwargs) -> Any:
    """
    Wrapper function to safely call API with rate limit handling.
    
    Args:
        func: The API function to call
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        The response from the API call
        
    Raises:
        RateLimitError: If rate limit exceeded after all retries
    """
    return func(*args, **kwargs)
