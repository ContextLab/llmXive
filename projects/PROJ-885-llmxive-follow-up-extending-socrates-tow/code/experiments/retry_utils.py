"""
Retry utilities for LLM inference experiments.

Provides an exponential backoff retry mechanism for handling transient
failures during API calls or local model inference.
"""

import logging
import time
from typing import Callable, TypeVar, Optional, Any, Tuple, Union
from functools import wraps

# Configure logger for this module
logger = logging.getLogger(__name__)

# Generic type for decorated functions
T = TypeVar('T')


class RetryError(Exception):
    """Exception raised when all retry attempts are exhausted."""
    def __init__(self, message: str, last_exception: Optional[Exception] = None):
        super().__init__(message)
        self.last_exception = last_exception


def exponential_backoff_retry(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retry_exceptions: Optional[Tuple[Type[Exception], ...]] = None
) -> Callable[..., T]:
    """
    Decorator to add exponential backoff retry logic to a function.

    Args:
        func: The function to wrap.
        max_retries: Maximum number of retry attempts (total attempts = max_retries + 1).
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay cap in seconds.
        exponential_base: Base for exponential calculation (default 2.0).
        jitter: If True, adds random jitter to delay to prevent thundering herd.
        retry_exceptions: Tuple of exception types to catch and retry.
                          Defaults to (TimeoutError, ConnectionError, OSError).

    Returns:
        The wrapped function with retry logic.

    Example:
        @exponential_backoff_retry(max_retries=3, base_delay=2.0)
        def infer_model(prompt):
            return model.generate(prompt)
    """
    if retry_exceptions is None:
        retry_exceptions = (TimeoutError, ConnectionError, OSError)

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        last_exception: Optional[Exception] = None

        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except retry_exceptions as e:
                last_exception = e
                if attempt == max_retries:
                    # All retries exhausted
                    error_msg = (
                        f"Function '{func.__name__}' failed after {max_retries + 1} attempts. "
                        f"Last error: {type(e).__name__}: {e}"
                    )
                    logger.error(error_msg, exc_info=True)
                    raise RetryError(error_msg, last_exception=e) from e

                # Calculate delay with exponential backoff
                delay = min(base_delay * (exponential_base ** attempt), max_delay)
                
                if jitter:
                    import random
                    delay = delay * (0.5 + random.random())  # Jitter between 0.5x and 1.5x

                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries + 1} failed for '{func.__name__}': "
                    f"{type(e).__name__}: {e}. Retrying in {delay:.2f}s..."
                )
                time.sleep(delay)

        # Should not reach here, but just in case
        raise RetryError(
            f"Unexpected error in retry loop for '{func.__name__}'", 
            last_exception
        )

    return wrapper


def retry_with_backoff(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    retry_exceptions: Optional[Tuple[Type[Exception], ...]] = None
) -> T:
    """
    Synchronous execution with retry logic (non-decorator version).

    Useful for one-off calls where decorating the function is not desired.

    Args:
        func: The callable to execute.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay cap in seconds.
        retry_exceptions: Tuple of exception types to retry on.

    Returns:
        The result of the function.

    Raises:
        RetryError: If all retries are exhausted.
    """
    if retry_exceptions is None:
        retry_exceptions = (TimeoutError, ConnectionError, OSError)

    last_exception: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            return func()
        except retry_exceptions as e:
            last_exception = e
            if attempt == max_retries:
                error_msg = (
                    f"Execution failed after {max_retries + 1} attempts. "
                    f"Last error: {type(e).__name__}: {e}"
                )
                logger.error(error_msg, exc_info=True)
                raise RetryError(error_msg, last_exception=e) from e

            delay = min(base_delay * (2 ** attempt), max_delay)
            logger.warning(
                f"Attempt {attempt + 1}/{max_retries + 1} failed: {type(e).__name__}: {e}. "
                f"Retrying in {delay:.2f}s..."
            )
            time.sleep(delay)

    raise RetryError("Unexpected loop exit", last_exception)