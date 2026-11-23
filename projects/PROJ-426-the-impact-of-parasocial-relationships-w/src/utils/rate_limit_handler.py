"""
Rate limit handling for API interactions, specifically designed for Pushshift API.
Integrates with retry_policy.py for exponential backoff strategies.
"""

import time
import logging
from typing import Optional, Callable, Any, Dict
from functools import wraps

from .retry_policy import retry_with_backoff, RetryConfig, calculate_backoff_delay

# Configure logger
logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """Exception raised when rate limit is exceeded and retries are exhausted."""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


def extract_retry_after(headers: Dict[str, Any]) -> Optional[int]:
    """
    Extract the 'Retry-After' header value from API response headers.
    
    Args:
        headers: Dictionary of response headers.
        
    Returns:
        Integer seconds to wait, or None if not present.
    """
    retry_after = headers.get('Retry-After')
    if retry_after is None:
        return None
    
    try:
        # Handle both integer seconds and HTTP date formats if necessary
        # Pushshift typically returns integer seconds
        return int(retry_after)
    except (ValueError, TypeError):
        logger.warning(f"Could not parse Retry-After header: {retry_after}")
        return None


def is_rate_limited(status_code: int) -> bool:
    """
    Check if the HTTP status code indicates a rate limit (429).
    
    Args:
        status_code: HTTP status code.
        
    Returns:
        True if status code is 429, False otherwise.
    """
    return status_code == 429


def handle_429_response(
    status_code: int, 
    headers: Dict[str, Any], 
    retry_config: RetryConfig, 
    attempt: int
) -> float:
    """
    Handle a 429 rate limit response by calculating backoff delay.
    
    Prioritizes the 'Retry-After' header if present, otherwise falls back
    to exponential backoff defined in retry_config.
    
    Args:
        status_code: HTTP status code (expected 429).
        headers: Response headers.
        retry_config: Configuration for retry logic.
        attempt: Current retry attempt number (0-indexed).
        
    Returns:
        Delay in seconds to wait before next attempt.
        
    Raises:
        RateLimitError: If max retries exceeded.
    """
    if not is_rate_limited(status_code):
        raise ValueError("handle_429_response should only be called for 429 status codes")

    # Check for Retry-After header first
    retry_after = extract_retry_after(headers)
    
    if retry_after is not None:
        logger.warning(f"Rate limit detected. Respect Retry-After header: {retry_after}s")
        return retry_after

    # Fallback to exponential backoff
    delay = calculate_backoff_delay(
        attempt=attempt,
        base_delay=retry_config.base_delay,
        max_delay=retry_config.max_delay
    )
    
    logger.warning(
        f"Rate limit detected. No Retry-After header. Using backoff: {delay}s "
        f"(attempt {attempt + 1}/{retry_config.max_retries})"
    )
    return delay


def rate_limit_handler(
    retry_config: Optional[RetryConfig] = None
) -> Callable:
    """
    Decorator to handle rate limiting (429) for API calls.
    
    Integrates with retry_policy to retry requests with exponential backoff
    when a 429 response is received.
    
    Args:
        retry_config: Optional RetryConfig. Defaults to standard backoff if None.
        
    Returns:
        Decorator function.
    """
    if retry_config is None:
        retry_config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(retry_config.max_retries + 1):
                try:
                    # Execute the function
                    result = func(*args, **kwargs)
                    
                    # If we get here without exception, check if we need to handle 429
                    # (Assuming the function returns a response object with status_code)
                    if hasattr(result, 'status_code'):
                        if is_rate_limited(result.status_code):
                            delay = handle_429_response(
                                result.status_code,
                                result.headers if hasattr(result, 'headers') else {},
                                retry_config,
                                attempt
                            )
                            if attempt == retry_config.max_retries:
                                raise RateLimitError(
                                    f"Rate limit exceeded after {attempt + 1} attempts",
                                    retry_after=delay
                                )
                            logger.info(f"Waiting {delay}s before retry...")
                            time.sleep(delay)
                            continue
                    
                    return result
                    
                except RateLimitError:
                    # Re-raise if we've already exhausted retries inside the loop
                    raise
                except Exception as e:
                    # For other exceptions, let retry_with_backoff handle them if configured,
                    # or re-raise immediately if not a retryable error type.
                    # For this specific handler, we focus on 429s. 
                    # If the underlying function raises a generic exception that isn't 429,
                    # we let it bubble up unless it's a known retryable error.
                    # To keep it simple and focused on T009: 429 handling.
                    # If the caller uses retry_with_backoff separately, this might double-retry.
                    # However, the task asks to integrate with retry_policy.
                    # We will assume the decorated function might raise a custom exception 
                    # representing a 429 if it doesn't return a response object.
                    
                    # Check if this is a 429-like exception
                    if hasattr(e, 'status_code') and is_rate_limited(e.status_code):
                        headers = getattr(e, 'headers', {})
                        delay = handle_429_response(
                            e.status_code,
                            headers,
                            retry_config,
                            attempt
                        )
                        if attempt == retry_config.max_retries:
                            raise RateLimitError(
                                f"Rate limit exceeded after {attempt + 1} attempts",
                                retry_after=delay
                            )
                        logger.info(f"Waiting {delay}s before retry...")
                        time.sleep(delay)
                        last_exception = e
                        continue
                    
                    # If not a 429, just raise
                    raise e

            # Should not reach here if logic is correct, but fallback
            if last_exception:
                raise RateLimitError("Rate limit exceeded after max retries", retry_after=0)
            raise RuntimeError("Unexpected state in rate_limit_handler")

        return wrapper
    return decorator


def safe_api_call(
    func: Callable,
    retry_config: Optional[RetryConfig] = None
) -> Callable:
    """
    Convenience wrapper to apply rate_limit_handler with default config.
    
    Args:
        func: The API call function to wrap.
        retry_config: Optional retry configuration.
        
    Returns:
        Wrapped function with rate limiting and retry logic.
    """
    return rate_limit_handler(retry_config)(func)
