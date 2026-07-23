"""
Logging utilities for the plant pathogen virulence pipeline.
Provides a configured logger and exponential backoff retry logic for network operations.
"""
import logging
import time
import random
from functools import wraps
from typing import Callable, Any, Optional, Tuple, Type
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError


# Configure a default logger for the package
logger = logging.getLogger("llmXive")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Returns a child logger for a specific module or component.
    
    Args:
        name: Optional name for the child logger (e.g., 'data.download').
              If None, returns the root 'llmXive' logger.
    
    Returns:
        A configured logging.Logger instance.
    """
    if name is None:
        return logger
    return logging.getLogger(f"llmXive.{name}")


def exponential_backoff_retry(
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (RequestException, Timeout, ConnectionError)
) -> Callable:
    """
    Decorator that implements exponential backoff retry logic for network operations.
    
    This decorator wraps a function (typically one performing HTTP requests) and
    retries execution upon catching specified exceptions. The delay between retries
    increases exponentially: delay = base_delay * (exponential_base ^ attempt)
    
    Args:
        max_retries: Maximum number of retry attempts (total attempts = max_retries + 1).
        base_delay: Initial delay in seconds before the first retry.
        max_delay: Maximum delay cap in seconds.
        exponential_base: Base for exponential calculation (default 2.0).
        jitter: If True, adds random jitter to the delay to prevent thundering herd.
        exceptions: Tuple of exception types to catch and retry on.
    
    Returns:
        A decorator function.
    
    Raises:
        The last caught exception if all retries are exhausted.
        Any non-specified exception immediately.
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
                        # Log failure after all retries
                        retry_logger = get_logger(func.__module__)
                        retry_logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries. "
                            f"Last error: {str(e)}"
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    # Add jitter if requested
                    if jitter:
                        delay = delay * (0.5 + random.random() * 0.5)
                    
                    retry_logger = get_logger(func.__module__)
                    retry_logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}. "
                        f"Retrying in {delay:.2f}s. Error: {str(e)}"
                    )
                    
                    time.sleep(delay)
            
            # Should not be reached, but just in case
            raise last_exception if last_exception else RuntimeError("Retry logic exhausted unexpectedly")
        
        return wrapper
    return decorator
