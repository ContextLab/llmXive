import logging
import time
import random
from typing import Callable, TypeVar, Optional, Tuple, Union
from functools import wraps

from utils.logging import get_logger, DataFetchError

logger = get_logger(__name__)

T = TypeVar('T')

class RetryConfig:
    """Configuration for retry logic."""
    def __init__(
        self,
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        exceptions: Tuple[type, ...] = (Exception,)
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.exceptions = exceptions

def calculate_delay(
    attempt: int,
    config: RetryConfig
) -> float:
    """
    Calculate the delay before the next retry attempt using exponential backoff.

    Args:
        attempt: The current attempt number (0-indexed).
        config: The RetryConfig object.

    Returns:
        The delay in seconds.
    """
    # Exponential backoff: base_delay * (exponential_base ^ attempt)
    delay = config.base_delay * (config.exponential_base ** attempt)

    # Cap at max_delay
    delay = min(delay, config.max_delay)

    # Add jitter if enabled
    if config.jitter:
        # Add random jitter between 0 and 50% of the calculated delay
        jitter_amount = delay * 0.5 * random.random()
        delay += jitter_amount

    return delay

def retry_with_backoff(
    config: Optional[RetryConfig] = None
) -> Callable:
    """
    Decorator to retry a function with exponential backoff.

    Args:
        config: Optional RetryConfig. If None, uses default settings.

    Returns:
        A decorator function.
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except config.exceptions as e:
                    last_exception = e
                    if attempt == config.max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {config.max_retries + 1} attempts: {e}"
                        )
                        # Raise a specific DataFetchError for network-related failures
                        if issubclass(type(e), (ConnectionError, TimeoutError, OSError)):
                            raise DataFetchError(
                                f"Failed to fetch data after {config.max_retries + 1} attempts: {e}"
                            ) from e
                        raise e

                    delay = calculate_delay(attempt, config)
                    logger.warning(
                        f"Attempt {attempt + 1}/{config.max_retries + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)

            # This part should theoretically not be reached due to the loop logic above
            raise last_exception

        return wrapper
    return decorator

def retry_request(
    func: Callable[..., T],
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> Callable[..., T]:
    """
    Convenience function to create a retry wrapper for network requests.

    Args:
        func: The function to wrap.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
        jitter: Whether to add random jitter.

    Returns:
        A wrapped function that retries on failure.
    """
    config = RetryConfig(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        jitter=jitter,
        exceptions=(ConnectionError, TimeoutError, OSError, DataFetchError)
    )
    return retry_with_backoff(config)(func)
