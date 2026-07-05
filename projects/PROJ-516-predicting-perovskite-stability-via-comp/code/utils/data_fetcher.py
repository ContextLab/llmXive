"""
Data fetcher utility with retry logic and exponential backoff.

This module provides functions to safely fetch data from external APIs,
handling transient failures with configurable retry strategies.
"""
import time
import logging
from typing import Optional, Callable, Any
from urllib.error import URLError, HTTPError
from urllib.request import urlopen, Request
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class FetchError(Exception):
    """Custom exception for data fetching failures."""
    pass


def fetch_with_retry(
    url: str,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    timeout: float = 30.0,
    headers: Optional[dict] = None
) -> bytes:
    """
    Fetch data from a URL with exponential backoff retry logic.

    Args:
        url: The URL to fetch data from.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds between retries.
        max_delay: Maximum delay in seconds between retries.
        backoff_factor: Multiplier for delay after each retry.
        timeout: Request timeout in seconds.
        headers: Optional HTTP headers to include in the request.

    Returns:
        The raw bytes of the response.

    Raises:
        FetchError: If all retry attempts fail or the URL is invalid.
        URLError: If the URL is malformed or unreachable after retries.
    """
    if not url:
        raise FetchError("URL cannot be empty")

    parsed_url = urlparse(url)
    if parsed_url.scheme not in ('http', 'https'):
        raise FetchError(f"Invalid URL scheme: {parsed_url.scheme}. Only http/https allowed.")

    request = Request(url, headers=headers or {})
    attempt = 0
    current_delay = base_delay

    while attempt <= max_retries:
        try:
            logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries + 1})")
            with urlopen(request, timeout=timeout) as response:
                if response.status == 200:
                    logger.info(f"Successfully fetched {url}")
                    return response.read()
                else:
                    # Non-200 status codes are treated as failures
                    logger.warning(f"HTTP {response.status} for {url}")
                    if attempt == max_retries:
                        raise FetchError(f"HTTP {response.status} after {max_retries + 1} attempts")
        except HTTPError as e:
            # HTTP errors (4xx, 5xx)
            logger.warning(f"HTTP Error {e.code}: {e.reason} for {url}")
            if e.code < 500:
                # Client errors (4xx) are usually not retryable
                raise FetchError(f"Client error {e.code}: {e.reason}")
            if attempt == max_retries:
                raise FetchError(f"HTTP {e.code} after {max_retries + 1} attempts")
        except URLError as e:
            # Network errors, DNS failures, etc.
            logger.warning(f"URL Error for {url}: {e.reason}")
            if attempt == max_retries:
                raise FetchError(f"URL Error after {max_retries + 1} attempts: {e.reason}")
        except TimeoutError:
            logger.warning(f"Timeout for {url}")
            if attempt == max_retries:
                raise FetchError(f"Timeout after {max_retries + 1} attempts")
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error fetching {url}: {e}")
            if attempt == max_retries:
                raise FetchError(f"Unexpected error after {max_retries + 1} attempts: {e}")

        # Wait before retrying
        if attempt < max_retries:
            logger.info(f"Retrying in {current_delay:.2f} seconds...")
            time.sleep(current_delay)
            current_delay = min(current_delay * backoff_factor, max_delay)

        attempt += 1

    # Should not reach here, but just in case
    raise FetchError(f"Failed to fetch {url} after {max_retries + 1} attempts")


def fetch_text_with_retry(
    url: str,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    timeout: float = 30.0,
    headers: Optional[dict] = None,
    encoding: str = 'utf-8'
) -> str:
    """
    Fetch text data from a URL with exponential backoff retry logic.

    Args:
        url: The URL to fetch data from.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds between retries.
        max_delay: Maximum delay in seconds between retries.
        backoff_factor: Multiplier for delay after each retry.
        timeout: Request timeout in seconds.
        headers: Optional HTTP headers to include in the request.
        encoding: Character encoding for the response text.

    Returns:
        The response text decoded as a string.

    Raises:
        FetchError: If all retry attempts fail or the URL is invalid.
    """
    raw_data = fetch_with_retry(
        url,
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
        timeout=timeout,
        headers=headers
    )
    return raw_data.decode(encoding)