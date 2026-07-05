"""
Utility functions for the llmXive project.
Provides logging configuration, exponential backoff retry logic, and deterministic seed pinning.
"""

import logging
import random
import time
import os
from typing import Callable, TypeVar, List, Any, Optional
from functools import wraps
import numpy as np
import requests
from requests.exceptions import RequestException, HTTPError, Timeout

# Type variable for generic retry wrapper
T = TypeVar('T')

# Default configuration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_SEED = 42
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # seconds
MAX_BACKOFF = 64.0     # seconds
BACKOFF_FACTOR = 2.0

# Global seed state
_seed_initialized = False


def setup_logging(
    level: int = DEFAULT_LOG_LEVEL,
    log_file: Optional[str] = None,
    format_str: str = DEFAULT_LOG_FORMAT
) -> logging.Logger:
    """
    Configures the root logger with the specified level and format.
    Optionally writes logs to a file.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Path to a log file. If None, logs to console only.
        format_str: Format string for log messages.

    Returns:
        The configured root logger instance.
    """
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates in interactive environments
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(format_str))
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(format_str))
        logger.addHandler(file_handler)

    return logger


def pin_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Pins the random seed for reproducibility across numpy, random, and os.environ (if needed).
    
    Args:
        seed: Integer seed value.
    """
    global _seed_initialized
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    _seed_initialized = True


def retry_with_exponential_backoff(
    max_retries: int = MAX_RETRIES,
    initial_backoff: float = INITIAL_BACKOFF,
    max_backoff: float = MAX_BACKOFF,
    backoff_factor: float = BACKOFF_FACTOR,
    exceptions: tuple = (RequestException, Timeout, HTTPError)
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that retries a function with exponential backoff on specified exceptions.
    
    Args:
        max_retries: Maximum number of retry attempts.
        initial_backoff: Initial wait time in seconds.
        max_backoff: Maximum wait time in seconds.
        backoff_factor: Multiplier for the backoff time (e.g., 2.0 doubles the wait).
        exceptions: Tuple of exception classes to catch and retry on.

    Returns:
        A decorator function.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            current_backoff = initial_backoff

            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logging.getLogger(func.__module__).error(
                            f"Failed after {max_retries} attempts: {e}"
                        )
                        raise e
                    
                    # Log retry attempt
                    logging.getLogger(func.__module__).warning(
                        f"Attempt {attempt} failed: {e}. Retrying in {current_backoff:.2f}s..."
                    )
                    
                    time.sleep(current_backoff)
                    current_backoff = min(current_backoff * backoff_factor, max_backoff)
            
            # Should not be reached, but for type safety
            raise last_exception  # type: ignore
        return wrapper
    return decorator


def fetch_with_retry(
    url: str,
    method: str = "GET",
    max_retries: int = MAX_RETRIES,
    timeout: float = 30.0,
    **kwargs: Any
) -> requests.Response:
    """
    Fetches a URL with automatic retries using exponential backoff for network errors.
    
    Args:
        url: The URL to fetch.
        method: HTTP method (GET, POST, etc.).
        max_retries: Maximum number of retry attempts.
        timeout: Request timeout in seconds.
        **kwargs: Additional arguments passed to requests.request.

    Returns:
        The requests.Response object for a successful request.

    Raises:
        requests.exceptions.RequestException: If all retries fail.
    """
    @retry_with_exponential_backoff(
        max_retries=max_retries,
        exceptions=(RequestException, Timeout, HTTPError)
    )
    def _do_request() -> requests.Response:
        response = requests.request(method, url, timeout=timeout, **kwargs)
        # Raise an HTTPError if the status is 4xx, 5xx
        response.raise_for_status()
        return response

    return _do_request()