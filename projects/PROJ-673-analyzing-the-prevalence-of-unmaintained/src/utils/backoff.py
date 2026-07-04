"""
Utility functions for exponential backoff retry logic.
"""
import time
import random
from typing import Callable, Any, Optional
from functools import wraps


def exponential_backoff(
    retries: int = 3,
    initial_delay: float = 1.0,
    multiplier: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> Callable:
    """
    Decorator to apply exponential backoff retry logic to a function.

    Args:
        retries: Maximum number of retry attempts (default: 3).
        initial_delay: Initial delay in seconds before the first retry (default: 1.0).
        multiplier: Multiplier for the delay after each retry (default: 2.0).
        max_delay: Maximum delay in seconds between retries (default: 60.0).
        jitter: If True, adds random jitter (0-25%) to the delay to prevent thundering herd.

    Returns:
        A decorator that wraps the target function with retry logic.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == retries:
                        # Max retries reached, raise the exception
                        raise

                    # Calculate next delay with jitter if enabled
                    if jitter:
                        jitter_factor = random.uniform(0.0, 0.25)
                        delay_with_jitter = delay * (1 + jitter_factor)
                    else:
                        delay_with_jitter = delay

                    # Cap delay at max_delay
                    actual_delay = min(delay_with_jitter, max_delay)

                    # Wait before retrying
                    time.sleep(actual_delay)

                    # Increase delay for next attempt
                    delay *= multiplier
                    delay = min(delay, max_delay)

            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
            return None
        return wrapper
    return decorator


def calculate_backoff_delay(
    attempt: int,
    initial_delay: float = 1.0,
    multiplier: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True
) -> float:
    """
    Calculate the backoff delay for a specific attempt number.

    This is a utility function to calculate delays without the decorator overhead,
    useful for manual retry loops.

    Args:
        attempt: The current attempt number (0-indexed, 0 is the first attempt).
        initial_delay: Initial delay in seconds (default: 1.0).
        multiplier: Multiplier for the delay (default: 2.0).
        max_delay: Maximum delay in seconds (default: 60.0).
        jitter: If True, adds random jitter (0-25%) to the delay.

    Returns:
        The calculated delay in seconds.
    """
    if attempt < 0:
        raise ValueError("Attempt number must be non-negative")

    # Calculate base delay
    delay = initial_delay * (multiplier ** attempt)

    # Apply cap
    delay = min(delay, max_delay)

    # Apply jitter if requested
    if jitter:
        jitter_factor = random.uniform(0.0, 0.25)
        delay = delay * (1 + jitter_factor)
        # Ensure jitter doesn't push us over max_delay
        delay = min(delay, max_delay)

    return delay
