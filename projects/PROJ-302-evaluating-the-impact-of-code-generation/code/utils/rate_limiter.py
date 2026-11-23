"""
Rate limiter for GitHub API with exponential backoff strategy.

Implements a limited number of retries with exponential backoff to handle
rate limiting and transient errors from the GitHub API.
"""

import time
import logging
from typing import Optional, Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)

# Configuration constants
MAX_RETRIES = 5  # Limited number of retries as per spec Edge Cases
INITIAL_BACKOFF = 1.0  # Initial backoff in seconds
BACKOFF_MULTIPLIER = 2.0  # Exponential backoff multiplier
MAX_BACKOFF = 60.0  # Maximum backoff cap in seconds


class RateLimitError(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


class MaxRetriesExceededError(Exception):
    """Exception raised when maximum retries have been exceeded."""
    pass


def exponential_backoff_with_retry(
    func: Callable,
    max_retries: int = MAX_RETRIES,
    initial_backoff: float = INITIAL_BACKOFF,
    backoff_multiplier: float = BACKOFF_MULTIPLIER,
    max_backoff: float = MAX_BACKOFF,
    retryable_exceptions: tuple = (RateLimitError, ConnectionError, TimeoutError)
) -> Callable:
    """
    Decorator that implements exponential backoff retry logic.
    
    Args:
        func: The function to wrap with retry logic
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff time in seconds
        backoff_multiplier: Multiplier for exponential backoff
        max_backoff: Maximum backoff time in seconds
        retryable_exceptions: Tuple of exception types that trigger a retry
    
    Returns:
        Wrapped function with retry logic
    
    Raises:
        MaxRetriesExceededError: If all retry attempts fail
        Exception: Any non-retryable exception raised by the function
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        backoff_time = initial_backoff
        last_exception = None
        
        for attempt in range(max_retries + 1):  # +1 to include the initial attempt
            try:
                return func(*args, **kwargs)
            except retryable_exceptions as e:
                last_exception = e
                
                if attempt == max_retries:
                    # All retries exhausted
                    logger.error(
                        f"Max retries ({max_retries}) exceeded for {func.__name__}. "
                        f"Last error: {str(e)}"
                    )
                    raise MaxRetriesExceededError(
                        f"Failed after {max_retries} retries. Last error: {str(e)}"
                    ) from e
                
                # Calculate next backoff time
                time.sleep(backoff_time)
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}. "
                    f"Retrying in {backoff_time:.2f}s. Error: {str(e)}"
                )
                
                # Exponential backoff with cap
                backoff_time = min(backoff_time * backoff_multiplier, max_backoff)
            except Exception as e:
                # Non-retryable exception, re-raise immediately
                logger.error(f"Non-retryable error in {func.__name__}: {str(e)}")
                raise
        
        # Should never reach here, but just in case
        raise MaxRetriesExceededError("Unexpected retry loop termination")
    
    return wrapper


class RateLimiter:
    """
    Rate limiter class for managing API calls with exponential backoff.
    
    This class provides methods to make API calls while respecting rate limits
    and implementing exponential backoff for retries.
    """
    
    def __init__(
        self,
        max_retries: int = MAX_RETRIES,
        initial_backoff: float = INITIAL_BACKOFF,
        backoff_multiplier: float = BACKOFF_MULTIPLIER,
        max_backoff: float = MAX_BACKOFF
    ):
        """
        Initialize the rate limiter.
        
        Args:
            max_retries: Maximum number of retry attempts
            initial_backoff: Initial backoff time in seconds
            backoff_multiplier: Multiplier for exponential backoff
            max_backoff: Maximum backoff time in seconds
        """
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.backoff_multiplier = backoff_multiplier
        self.max_backoff = max_backoff
    
    def execute_with_backoff(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a function with exponential backoff retry logic.
        
        Args:
            func: The function to execute
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
        
        Returns:
            The result of the function call
        
        Raises:
            MaxRetriesExceededError: If all retry attempts fail
            Exception: Any non-retryable exception raised by the function
        """
        backoff_time = self.initial_backoff
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except (RateLimitError, ConnectionError, TimeoutError) as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    logger.error(
                        f"Max retries ({self.max_retries}) exceeded. "
                        f"Last error: {str(e)}"
                    )
                    raise MaxRetriesExceededError(
                        f"Failed after {self.max_retries} retries. Last error: {str(e)}"
                    ) from e
                
                # Sleep with exponential backoff
                time.sleep(backoff_time)
                logger.warning(
                    f"Attempt {attempt + 1}/{self.max_retries + 1} failed. "
                    f"Retrying in {backoff_time:.2f}s. Error: {str(e)}"
                )
                
                # Update backoff time with cap
                backoff_time = min(backoff_time * self.backoff_multiplier, self.max_backoff)
            except Exception as e:
                # Non-retryable exception
                logger.error(f"Non-retryable error: {str(e)}")
                raise
        
        raise MaxRetriesExceededError("Unexpected retry loop termination")

def parse_rate_limit_headers(headers: dict) -> dict:
    """
    Parse rate limit information from GitHub API response headers.
    
    Args:
        headers: Dictionary of response headers
    
    Returns:
        Dictionary containing rate limit information:
        - limit: Total requests allowed per window
        - remaining: Requests remaining in current window
        - reset: Unix timestamp when the window resets
    """
    return {
        'limit': int(headers.get('X-RateLimit-Limit', 0)),
        'remaining': int(headers.get('X-RateLimit-Remaining', 0)),
        'reset': int(headers.get('X-RateLimit-Reset', 0)),
        'used': int(headers.get('X-RateLimit-Used', 0))
    }

def should_retry(status_code: int) -> bool:
    """
    Determine if a request should be retried based on HTTP status code.
    
    Args:
        status_code: HTTP status code from the response
    
    Returns:
        True if the request should be retried, False otherwise
    """
    # Retry on 403 (rate limit), 429 (too many requests), 500-599 (server errors)
    return status_code in (403, 429) or (500 <= status_code < 600)