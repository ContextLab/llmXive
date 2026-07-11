"""
Retry utilities for external API calls with exponential backoff.

This module provides a decorator and a helper function to handle transient
failures when accessing external services (e.g., MAST archive via astroquery).
It implements exponential backoff with jitter to prevent thundering herd
issues and respect rate limits.
"""

import time
import random
import logging
from functools import wraps
from typing import Callable, Type, Tuple, Any, Optional, Union
from requests.exceptions import RequestException, Timeout, ConnectionError
from urllib3.exceptions import MaxRetryError, ProtocolError

# Import logger from the project's existing logging infrastructure
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Default configuration for retry logic
DEFAULT_MAX_RETRIES = 5
DEFAULT_BASE_DELAY = 1.0  # seconds
DEFAULT_MAX_DELAY = 60.0  # seconds
DEFAULT_JITTER_FACTOR = 0.1  # 10% jitter

# Specific exceptions to catch and retry
RETRYABLE_EXCEPTIONS = (
    RequestException,
    Timeout,
    ConnectionError,
    MaxRetryError,
    ProtocolError,
    # astroquery specific network issues often bubble up as these
    OSError,
)


def calculate_backoff(
    attempt: int,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    jitter_factor: float = DEFAULT_JITTER_FACTOR,
) -> float:
    """
    Calculate the delay before the next retry attempt using exponential backoff
    with jitter.

    Args:
        attempt: The current attempt number (0-indexed).
        base_delay: The initial delay in seconds.
        max_delay: The maximum delay cap in seconds.
        jitter_factor: Factor to multiply random jitter by (0.0 to 1.0).

    Returns:
        The delay in seconds before the next attempt.
    """
    # Exponential backoff: base_delay * (2 ^ attempt)
    exp_delay = base_delay * (2 ** attempt)
    
    # Cap at max_delay
    capped_delay = min(exp_delay, max_delay)
    
    # Add jitter: random value between 0 and jitter_factor * capped_delay
    jitter = random.uniform(0, jitter_factor * capped_delay)
    
    return capped_delay + jitter


def retry_with_backoff(
    max_retries: int = DEFAULT_MAX_RETRIES,
    exceptions: Tuple[Type[Exception], ...] = RETRYABLE_EXCEPTIONS,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    jitter_factor: float = DEFAULT_JITTER_FACTOR,
    log_level: int = logging.WARNING,
) -> Callable:
    """
    Decorator to retry a function with exponential backoff on specified exceptions.

    Args:
        max_retries: Maximum number of retry attempts (total attempts = max_retries + 1).
        exceptions: Tuple of exception types to catch and retry.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay cap in seconds.
        jitter_factor: Factor for random jitter.
        log_level: Logging level for retry events (default WARNING).

    Returns:
        A decorator function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries + 1} attempts: {e}",
                            exc_info=True,
                        )
                        raise
                    
                    delay = calculate_backoff(
                        attempt, base_delay, max_delay, jitter_factor
                    )
                    
                    logger.log(
                        log_level,
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}. "
                        f"Retrying in {delay:.2f}s... (Error: {e})",
                    )
                    time.sleep(delay)
            
            # Should technically never reach here due to the raise in the loop
            raise last_exception if last_exception else RuntimeError("Unknown retry failure")
        
        return wrapper
    return decorator


def retry_call(
    func: Callable,
    *args: Any,
    max_retries: int = DEFAULT_MAX_RETRIES,
    exceptions: Tuple[Type[Exception], ...] = RETRYABLE_EXCEPTIONS,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    jitter_factor: float = DEFAULT_JITTER_FACTOR,
    **kwargs: Any,
) -> Any:
    """
    Execute a function with retry logic and exponential backoff.
    
    This is a non-decorator alternative for one-off calls.

    Args:
        func: The function to execute.
        *args: Positional arguments to pass to func.
        max_retries: Maximum number of retry attempts.
        exceptions: Tuple of exception types to catch.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay cap in seconds.
        jitter_factor: Factor for random jitter.
        **kwargs: Keyword arguments to pass to func.

    Returns:
        The return value of func if successful.

    Raises:
        The last exception encountered if all retries fail.
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            
            if attempt == max_retries:
                logger.error(
                    f"Function {func.__name__} failed after {max_retries + 1} attempts: {e}",
                    exc_info=True,
                )
                raise
            
            delay = calculate_backoff(
                attempt, base_delay, max_delay, jitter_factor
            )
            
            logger.log(
                logging.WARNING,
                f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}. "
                f"Retrying in {delay:.2f}s... (Error: {e})",
            )
            time.sleep(delay)
    
    raise last_exception if last_exception else RuntimeError("Unknown retry failure")
