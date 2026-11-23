"""
Retry utilities for external API calls (NCBI, ERA5, NOAA).
Implements exponential backoff with jitter to handle rate limits.
"""
import time
import random
import logging
from typing import Callable, Any, Optional, Tuple, Type
from functools import wraps

from .logger import get_logger

logger = get_logger(__name__)


class RetryError(Exception):
    """Raised when all retry attempts fail."""
    pass


def exponential_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> float:
    """
    Calculate delay for exponential backoff.

    Args:
        attempt: The current attempt number (0-indexed).
        base_delay: Base delay in seconds.
        max_delay: Maximum delay cap in seconds.
        jitter: If True, add random jitter (0.0 to 1.0 * delay).

    Returns:
        Delay in seconds.
    """
    delay = min(base_delay * (2 ** attempt), max_delay)
    if jitter:
        delay = delay * (0.5 + random.random() * 0.5)
    return delay


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorator to retry a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts (total attempts = max_retries + 1).
        base_delay: Base delay in seconds.
        max_delay: Maximum delay cap in seconds.
        exceptions: Tuple of exception types to catch and retry.

    Returns:
        Decorated function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )
                        raise RetryError(
                            f"Function {func.__name__} failed after {max_retries + 1} attempts: {e}"
                        ) from e

                    delay = exponential_backoff(
                        attempt,
                        base_delay=base_delay,
                        max_delay=max_delay
                    )
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
            raise RetryError("Unexpected retry loop exit")
        return wrapper
    return decorator


def retry_function(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    *args: Any,
    **kwargs: Any
) -> Any:
    """
    Execute a function with retry logic and exponential backoff.

    Args:
        func: The function to execute.
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds.
        max_delay: Maximum delay cap in seconds.
        exceptions: Tuple of exception types to catch and retry.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.

    Returns:
        The result of the function.

    Raises:
        RetryError: If all retries fail.
    """
    last_exception: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            last_exception = e
            if attempt == max_retries:
                logger.error(
                    f"Function {func.__name__} failed after {max_retries + 1} attempts: {e}"
                )
                raise RetryError(
                    f"Function {func.__name__} failed after {max_retries + 1} attempts: {e}"
                ) from e

            delay = exponential_backoff(
                attempt,
                base_delay=base_delay,
                max_delay=max_delay
            )
            logger.warning(
                f"Function {func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                f"Retrying in {delay:.2f}s..."
            )
            time.sleep(delay)
    raise RetryError("Unexpected retry loop exit")