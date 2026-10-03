"""
Retry Policy Module for llmXive Pipeline.

Implements exponential backoff strategies for API calls to handle transient failures
and rate limiting gracefully.
"""

import time
import logging
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps
import random

from .logging import get_logger

# Configure logger for this module
logger = get_logger(__name__)


class RetryConfig:
    """
    Configuration object for retry logic.

    Attributes:
        max_retries (int): Maximum number of retry attempts.
        base_delay (float): Base delay in seconds before the first retry.
        max_delay (float): Maximum delay cap in seconds.
        exponential_base (float): Base for exponential backoff calculation.
        jitter (bool): Whether to add random jitter to delay to prevent thundering herd.
        exceptions (Tuple[Type[Exception], ...]): Tuple of exception types to catch and retry.
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        exceptions: Optional[Tuple[Type[Exception], ...]] = None
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.exceptions = exceptions if exceptions else (Exception,)

    def __repr__(self) -> str:
        return (
            f"RetryConfig(max_retries={self.max_retries}, "
            f"base_delay={self.base_delay}, max_delay={self.max_delay}, "
            f"jitter={self.jitter})"
        )


def calculate_backoff_delay(
    attempt: int,
    config: RetryConfig
) -> float:
    """
    Calculate the delay duration for a specific retry attempt using exponential backoff.

    Formula: min(max_delay, base_delay * (exponential_base ^ attempt))
    If jitter is enabled, adds a random factor between 0 and 1 to the delay.

    Args:
        attempt (int): The current attempt number (0-indexed for the first retry).
        config (RetryConfig): The configuration object containing backoff parameters.

    Returns:
        float: The calculated delay in seconds.
    """
    delay = config.base_delay * (config.exponential_base ** attempt)

    if config.jitter:
        # Add jitter: random value between 0 and the calculated delay
        delay = delay * (0.5 + 0.5 * random.random())

    return min(delay, config.max_delay)


def retry_with_backoff(
    config: Optional[RetryConfig] = None
) -> Callable:
    """
    Decorator to retry a function with exponential backoff on specified exceptions.

    Args:
        config (RetryConfig, optional): Configuration for retry behavior.
            Defaults to RetryConfig(max_retries=3, base_delay=1.0, max_delay=60.0).

    Returns:
        Callable: The wrapped function with retry logic.

    Example:
        @retry_with_backoff(RetryConfig(max_retries=3, base_delay=1.0))
        def fetch_data():
            ...
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None

            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except config.exceptions as e:
                    last_exception = e

                    if attempt < config.max_retries:
                        delay = calculate_backoff_delay(attempt, config)
                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_retries} failed "
                            f"for {func.__name__}: {str(e)}. Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_retries + 1} attempts failed for {func.__name__}. "
                            f"Last error: {str(e)}"
                        )
                        raise

            # Should not be reached, but satisfies type checkers
            raise last_exception if last_exception else RuntimeError("Retry loop exhausted unexpectedly")

        return wrapper
    return decorator