import time
import random
from typing import Callable, Any

def exponential_backoff(
    func: Callable[..., Any],
    *args: Any,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    multiplier: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    **kwargs: Any
) -> Any:
    """
    Execute a function with exponential backoff and jitter on failure.

    Args:
        func: The function to execute.
        *args: Positional arguments to pass to the function.
        max_retries: Maximum number of retry attempts (default: 3).
        initial_delay: Initial delay in seconds (default: 1.0).
        multiplier: Delay multiplier for each retry (default: 2.0).
        max_delay: Maximum delay cap in seconds (default: 60.0).
        jitter: Whether to add random jitter to the delay (default: True).
        **kwargs: Keyword arguments to pass to the function.

    Returns:
        The return value of the function if successful.

    Raises:
        Exception: The last exception raised if all retries fail.
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt == max_retries:
                break

            # Calculate delay with jitter
            if jitter:
                delay_with_jitter = delay + random.uniform(0, delay * 0.1)
            else:
                delay_with_jitter = delay

            # Cap at max_delay
            actual_delay = min(delay_with_jitter, max_delay)

            time.sleep(actual_delay)
            delay *= multiplier

    raise last_exception
