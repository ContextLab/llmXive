"""
Utility functions for data fetching with robust error handling.

This module provides retry logic with exponential backoff for network requests,
ensuring resilience against transient failures during API/FTP fetches.
"""
import time
import logging
import urllib.request
import urllib.error
from typing import Callable, Any, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class FetchError(Exception):
    """
    Custom exception for fetch failures after all retries are exhausted.
    
    Attributes:
        message (str): Human-readable error message.
        last_exception (Exception): The underlying exception that caused the final failure.
        attempts (int): Number of attempts made before giving up.
    """
    def __init__(self, message: str, last_exception: Exception, attempts: int):
        super().__init__(message)
        self.message = message
        self.last_exception = last_exception
        self.attempts = attempts

    def __str__(self) -> str:
        return (f"{self.message} (Last error: {self.last_exception}, "
                f"Attempts: {self.attempts})")


def fetch_with_backoff(
    url: str,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    timeout: float = 30.0
) -> str:
    """
    Fetch content from a URL with exponential backoff retry logic.
    
    This function attempts to fetch text content from the given URL. If a transient
    network error occurs (e.g., connection timeout, 5xx server error), it retries
    with an exponentially increasing delay until max_retries is reached.
    
    Args:
        url (str): The URL to fetch.
        max_retries (int): Maximum number of retry attempts.
        base_delay (float): Initial delay in seconds before the first retry.
        max_delay (float): Maximum delay cap in seconds.
        exponential_base (float): Base for exponential delay calculation.
        jitter (bool): If True, adds random jitter to delay to prevent thundering herd.
        timeout (float): Request timeout in seconds.
    
    Returns:
        str: The decoded text content of the response.
    
    Raises:
        FetchError: If all retries are exhausted or a non-retryable error occurs.
        ValueError: If the URL is invalid or empty.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    attempt = 0
    last_exception: Optional[Exception] = None

    while attempt <= max_retries:
        try:
            logger.info(f"Fetching {url} (Attempt {attempt + 1}/{max_retries + 1})")
            
            with urllib.request.urlopen(url, timeout=timeout) as response:
                # Check for HTTP errors
                if response.status >= 400:
                    # 4xx are client errors, usually not retryable unless 429
                    if response.status == 429:  # Too Many Requests
                        pass  # Treat as retryable
                    elif response.status >= 500:
                        pass  # Retryable server error
                    else:
                        raise FetchError(
                            f"Non-retryable HTTP error {response.status}",
                            urllib.error.HTTPError(url, response.status, response.reason, None, None),
                            attempt + 1
                        )
                
                content = response.read().decode('utf-8')
                logger.info(f"Successfully fetched {url}")
                return content

        except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError) as e:
            last_exception = e
            attempt += 1
            
            if attempt > max_retries:
                logger.error(f"Failed to fetch {url} after {max_retries} retries")
                raise FetchError(
                    f"Failed to fetch {url} after {max_retries} retries",
                    last_exception,
                    attempt
                ) from last_exception

            # Calculate delay with exponential backoff
            delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
            
            if jitter:
                import random
                delay = delay * (0.5 + random.random())  # Add +/- 50% jitter
            
            logger.warning(
                f"Transient error fetching {url}: {e}. "
                f"Retrying in {delay:.2f}s (Attempt {attempt}/{max_retries})"
            )
            time.sleep(delay)

    # Should not reach here, but safe fallback
    raise FetchError(
        f"Unexpected termination of fetch loop for {url}",
        last_exception or Exception("Unknown error"),
        attempt
    )


def fetch_with_backoff_bytes(
    url: str,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    timeout: float = 30.0
) -> bytes:
    """
    Fetch binary content from a URL with exponential backoff retry logic.
    
    Similar to `fetch_with_backoff`, but returns raw bytes instead of decoded text.
    Useful for downloading files like images, archives, or binary data formats.
    
    Args:
        url (str): The URL to fetch.
        max_retries (int): Maximum number of retry attempts.
        base_delay (float): Initial delay in seconds before the first retry.
        max_delay (float): Maximum delay cap in seconds.
        exponential_base (float): Base for exponential delay calculation.
        jitter (bool): If True, adds random jitter to delay to prevent thundering herd.
        timeout (float): Request timeout in seconds.
    
    Returns:
        bytes: The raw binary content of the response.
    
    Raises:
        FetchError: If all retries are exhausted or a non-retryable error occurs.
        ValueError: If the URL is invalid or empty.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    attempt = 0
    last_exception: Optional[Exception] = None

    while attempt <= max_retries:
        try:
            logger.info(f"Fetching binary data from {url} (Attempt {attempt + 1}/{max_retries + 1})")
            
            with urllib.request.urlopen(url, timeout=timeout) as response:
                if response.status >= 400:
                    if response.status == 429 or response.status >= 500:
                        pass  # Retryable
                    else:
                        raise FetchError(
                            f"Non-retryable HTTP error {response.status}",
                            urllib.error.HTTPError(url, response.status, response.reason, None, None),
                            attempt + 1
                        )
                
                content = response.read()
                logger.info(f"Successfully fetched binary data from {url} ({len(content)} bytes)")
                return content

        except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError) as e:
            last_exception = e
            attempt += 1
            
            if attempt > max_retries:
                logger.error(f"Failed to fetch {url} after {max_retries} retries")
                raise FetchError(
                    f"Failed to fetch {url} after {max_retries} retries",
                    last_exception,
                    attempt
                ) from last_exception

            # Calculate delay with exponential backoff
            delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
            
            if jitter:
                import random
                delay = delay * (0.5 + random.random())
            
            logger.warning(
                f"Transient error fetching {url}: {e}. "
                f"Retrying in {delay:.2f}s (Attempt {attempt}/{max_retries})"
            )
            time.sleep(delay)

    raise FetchError(
        f"Unexpected termination of fetch loop for {url}",
        last_exception or Exception("Unknown error"),
        attempt
    )