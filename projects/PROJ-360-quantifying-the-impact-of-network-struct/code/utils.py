"""
utils.py
--------
Shared utility functions for the project.

Provides:
- Deterministic seed pinning.
- Exponential‑backoff retry decorator.
- Flexible logger setup / simple logger wrapper.
- A lightweight API‑rate‑limiter.
"""

import logging
import random
import time
import os
from typing import Callable, TypeVar, Any, Optional
from functools import wraps

import numpy as np

T = TypeVar("T")


def setup_logging(
    logger_or_level: Any = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Configure a ``logging.Logger`` instance.

    The function is deliberately tolerant of the two calling styles that
    exist in the code base:

    1. ``setup_logging(level=logging.DEBUG)`` – only a log level is supplied.
    2. ``setup_logging(existing_logger, level=logging.DEBUG)`` – an existing
       logger instance is supplied together with a log level.

    If ``logger_or_level`` is a ``logging.Logger`` the function configures that
    logger; otherwise a new logger named ``"llmXive"`` is created.  The logger
    is given a single ``StreamHandler`` (if it does not already have one) and
    the requested log level is applied.

    Parameters
    ----------
    logger_or_level :
        Either a ``logging.Logger`` instance or an ``int`` representing the
        desired log level.  If omitted, a new logger named ``"llmXive"`` is
        created with the default ``INFO`` level.
    level :
        The log level to apply when ``logger_or_level`` is a ``Logger``.
        Ignored when ``logger_or_level`` is an ``int`` or ``None``.

    Returns
    -------
    logging.Logger
        The configured logger.
    """
    # Determine whether the first argument is a logger or a level.
    if isinstance(logger_or_level, logging.Logger):
        logger = logger_or_level
        log_level = level
    else:
        logger = logging.getLogger("llmXive")
        # ``logger_or_level`` may be an int (explicit level) or ``None``.
        log_level = (
            logger_or_level
            if isinstance(logger_or_level, int)
            else level
        )

    logger.setLevel(log_level)

    # Attach a simple ``StreamHandler`` only once.
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def retry_with_exponential_backoff(
    func: Callable[..., T],
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
) -> Callable[..., T]:
    """
    Decorator that retries ``func`` with exponential back‑off.

    Parameters
    ----------
    func : Callable[..., T]
        Function to be wrapped.
    max_retries : int, optional
        Maximum number of attempts (default 5).
    base_delay : float, optional
        Initial delay in seconds (default 1.0).
    max_delay : float, optional
        Upper bound for the delay (default 60.0).
    exceptions : tuple, optional
        Exception types that trigger a retry (default ``Exception``).

    Returns
    -------
    Callable[..., T]
        Wrapped function that performs the retry logic.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        delay = base_delay
        last_exception = None
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                if attempt < max_retries - 1:
                    logging.warning(
                        f"Retry {attempt + 1}/{max_retries} for {func.__name__} after {delay:.1f}s"
                    )
                    time.sleep(delay)
                    delay = min(delay * 2, max_delay)
                else:
                    logging.error(f"Failed after {max_retries} retries: {e}")
                    raise
        # Should never reach here, but keep mypy happy.
        raise last_exception

    return wrapper


def pin_seed(seed: int = 42) -> None:
    """
    Pin random seeds across ``random``, ``numpy`` and the Python hash seed.

    This function is idempotent – calling it multiple times with the same
    ``seed`` does not change the deterministic state beyond the first call.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    logging.info(f"Random seeds pinned to {seed}")


def fetch_with_retry(
    url: str,
    headers: Optional[dict] = None,
    params: Optional[dict] = None,
    timeout: int = 30,
    max_retries: int = 5,
) -> Optional[dict]:
    """
    Perform an HTTP GET request with exponential back‑off.

    Returns the parsed JSON payload on success, or ``None`` if all retries
    fail.  The function logs failures but **does not** fabricate data.
    """
    import requests

    retry_func = retry_with_exponential_backoff(
        requests.get,
        max_retries=max_retries,
        exceptions=(requests.RequestException,),
    )
    try:
        response = retry_func(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except Exception as e:  # pragma: no cover – exercised via integration tests
        logging.error(f"Failed to fetch {url}: {e}")
        return None


class APIRateLimiter:
    """
    Simple rate‑limiter that enforces a minimum delay between API calls.

    Usage
    -----
    >>> limiter = APIRateLimiter(min_delay_seconds=1.0)
    >>> limiter.acquire()   # blocks if the previous call was <1 s ago
    """

    def __init__(self, min_delay_seconds: float = 1.0):
        self.min_delay = min_delay_seconds
        self._last_request_time: float = 0.0
        self._logger = logging.getLogger(__name__)

    def wait(self) -> None:
        """
        Block until ``self.min_delay`` seconds have elapsed since the last
        request.  If no request has been made yet, returns immediately.
        """
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        if elapsed < self.min_delay:
            sleep_time = self.min_delay - elapsed
            self._logger.debug(f"Rate limiter: waiting {sleep_time:.2f}s")
            time.sleep(sleep_time)

    def mark_request(self) -> None:
        """Record the current time as the moment a request was sent."""
        self._last_request_time = time.time()
        self._logger.debug(f"Rate limiter: request marked at {self._last_request_time}")

    def acquire(self) -> None:
        """Convenience method that waits then marks the request."""
        self.wait()
        self.mark_request()
