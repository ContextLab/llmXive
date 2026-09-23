"""
Exponential backoff utility for API retry logic.

Implements exponential backoff with jitter to prevent thundering herd
and respect rate limits as per FR-009.

Parameters:
- max_retries: 3 (per FR-009)
- initial_delay: 1 second
- multiplier: 2.0
- max_delay: 60 seconds
"""

import time
import random
from typing import Callable, Any, TypeVar, Optional

T = TypeVar('T')

# Constants as per FR-009 and specification
MAX_RETRIES = 3
INITIAL_DELAY = 1.0  # seconds
MULTIPLIER = 2.0
MAX_DELAY = 60.0  # seconds

def exponential_backoff(
    func: Callable[..., T],
    max_retries: int = MAX_RETRIES,
    initial_delay: float = INITIAL_DELAY,
    multiplier: float = MULTIPLIER,
    max_delay: float = MAX_DELAY,
    *args: Any,
    **kwargs: Any
) -> T:
    """
    Executes a function with exponential backoff retry logic.

    Args:
        func: The function to execute.
        max_retries: Maximum number of retry attempts (default: 3).
        initial_delay: Initial delay in seconds (default: 1.0).
        multiplier: Delay multiplier for each retry (default: 2.0).
        max_delay: Maximum delay cap in seconds (default: 60.0).
        *args: Positional arguments to pass to func.
        **kwargs: Keyword arguments to pass to func.

    Returns:
        The return value of the successful function call.

    Raises:
        Exception: Re-raises the last exception if all retries are exhausted.
    """
    last_exception = None
    current_delay = initial_delay

    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                # Calculate delay with jitter
                jitter = random.uniform(0, 0.1 * current_delay)
                sleep_time = min(current_delay + jitter, max_delay)
                time.sleep(sleep_time)
                current_delay *= multiplier
            else:
                # All retries exhausted
                raise

    # This line is theoretically unreachable due to the raise above,
    # but included for type safety in some strict analyzers.
    raise last_exception  # type: ignore