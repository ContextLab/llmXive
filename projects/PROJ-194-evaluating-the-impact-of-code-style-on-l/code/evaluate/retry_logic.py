"""
Retry logic for LLM inference to handle timeouts and transient failures.

Implements bounded retry attempts with exponential backoff for the CodeGen-2B
inference stage.
"""
import time
import logging
from typing import Callable, Any, Optional, TypeVar, List
from functools import wraps

# Define custom exceptions for clarity
class InferenceTimeoutError(Exception):
    """Raised when an inference request times out."""
    pass

class InferenceRateLimitError(Exception):
    """Raised when the model service returns a 429 rate limit error."""
    pass

class InferenceTransientError(Exception):
    """Raised for other transient inference failures."""
    pass

T = TypeVar('T')

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_DELAY = 1.0  # seconds
DEFAULT_MAX_DELAY = 10.0     # seconds
DEFAULT_BACKOFF_FACTOR = 2.0
DEFAULT_TIMEOUT = 60.0       # seconds per attempt

def retry_with_backoff(
    max_retries: int = DEFAULT_MAX_RETRIES,
    initial_delay: float = DEFAULT_INITIAL_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    timeout: float = DEFAULT_TIMEOUT,
    exceptions_to_retry: tuple = (InferenceTimeoutError, InferenceRateLimitError, InferenceTransientError)
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to retry a function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts.
        initial_delay: Initial delay in seconds before the first retry.
        max_delay: Maximum delay in seconds between retries.
        backoff_factor: Multiplier for the delay after each retry.
        timeout: Timeout in seconds for the wrapped function (if applicable).
        exceptions_to_retry: Tuple of exception types that trigger a retry.
        
    Returns:
        A decorator function.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    # Pass timeout to the function if it accepts it
                    # We assume the wrapped inference function accepts a 'timeout' kwarg
                    if timeout and 'timeout' not in kwargs:
                        kwargs['timeout'] = timeout
                        
                    return func(*args, **kwargs)
                except exceptions_to_retry as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}. "
                            f"Last error: {e}"
                        )
                        raise
                except Exception as e:
                    # Non-retryable exception, re-raise immediately
                    logger.error(f"Non-retryable error in {func.__name__}: {e}")
                    raise
            
            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected retry logic failure")

        return wrapper
    return decorator

def run_with_retry(
    func: Callable[..., T],
    *args,
    max_retries: int = DEFAULT_MAX_RETRIES,
    initial_delay: float = DEFAULT_INITIAL_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    timeout: float = DEFAULT_TIMEOUT,
    **kwargs
) -> T:
    """
    Execute a function with retry logic without using the decorator syntax.
    
    Useful for one-off execution or when the function is passed dynamically.
    """
    decorator = retry_with_backoff(
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
        timeout=timeout
    )
    wrapped_func = decorator(func)
    return wrapped_func(*args, **kwargs)

# Example usage and test runner
def run_retry_logic_test():
    """
    Test the retry logic with a mock function that fails a few times.
    """
    call_count = 0

    def failing_function(timeout=10):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise InferenceTimeoutError(f"Simulated timeout (attempt {call_count})")
        return {"success": True, "attempts": call_count}

    try:
        result = run_with_retry(
            failing_function,
            max_retries=3,
            initial_delay=0.1,
            max_delay=0.5
        )
        print(f"Test passed. Result: {result}")
        assert result["attempts"] == 3, "Expected 3 attempts"
    except Exception as e:
        print(f"Test failed: {e}")

def main():
    """Entry point for testing the retry logic module."""
    print("Running retry logic self-test...")
    run_retry_logic_test()
    print("Self-test completed.")

if __name__ == "__main__":
    main()