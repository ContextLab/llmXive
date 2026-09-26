"""
Utility functions for data fetching with robust error handling.

This module provides exponential backoff wrappers for API/FTP fetches
to handle transient network failures gracefully.
"""
import time
import logging
import urllib.request
import urllib.error
from typing import Callable, Any, Optional, Union
from pathlib import Path
import socket

logger = logging.getLogger(__name__)


class FetchError(Exception):
    """Custom exception for data fetching failures."""
    pass


def fetch_with_backoff(
    url: str,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    timeout: float = 30.0,
    extra_retry_codes: Optional[list] = None
) -> str:
    """
    Fetch content from a URL with exponential backoff retry logic.
    
    This function attempts to fetch text content from a URL, retrying on
    transient failures (network timeouts, HTTP 5xx, HTTP 429) with
    exponentially increasing delays between attempts.
    
    Args:
        url: The URL to fetch content from.
        max_retries: Maximum number of retry attempts (default: 5).
        base_delay: Initial delay in seconds between retries (default: 1.0).
        max_delay: Maximum delay cap in seconds (default: 60.0).
        timeout: Request timeout in seconds (default: 30.0).
        extra_retry_codes: Additional HTTP status codes to retry on.
        
    Returns:
        The fetched content as a string.
        
    Raises:
        FetchError: If all retry attempts fail or a non-retryable error occurs.
        urllib.error.URLError: If the URL is invalid or unreachable.
        urllib.error.HTTPError: If an HTTP error occurs that is not retryable.
    """
    retry_codes = {429, 500, 502, 503, 504}
    if extra_retry_codes:
        retry_codes.update(extra_retry_codes)
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries + 1})")
            
            req = urllib.request.Request(url, headers={'User-Agent': 'llmXive-Research/1.0'})
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                # Check HTTP status code
                status_code = response.getcode()
                if status_code in retry_codes and attempt < max_retries:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(
                        f"HTTP {status_code} received. Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    continue
                
                if status_code != 200:
                    raise FetchError(
                        f"HTTP {status_code} for {url} - not retryable"
                    )
                
                return response.read().decode('utf-8')
                
        except (urllib.error.HTTPError, urllib.error.URLError, socket.timeout, 
               ConnectionResetError, TimeoutError) as e:
            last_exception = e
            
            # Check if this is a retryable error
            if isinstance(e, urllib.error.HTTPError) and e.code in retry_codes:
                if attempt < max_retries:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(
                        f"HTTP {e.code} received. Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    continue
                else:
                    raise FetchError(
                        f"Failed after {max_retries + 1} attempts: HTTP {e.code} - {str(e)}"
                    ) from e
            
            elif isinstance(e, (urllib.error.URLError, socket.timeout, 
                               ConnectionResetError, TimeoutError)):
                if attempt < max_retries:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(
                        f"Network error: {type(e).__name__}. Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    continue
                else:
                    raise FetchError(
                        f"Failed after {max_retries + 1} attempts: {type(e).__name__} - {str(e)}"
                    ) from e
            
            else:
                # Non-retryable error
                raise FetchError(f"Fatal error fetching {url}: {str(e)}") from e
                
        except Exception as e:
            raise FetchError(f"Unexpected error fetching {url}: {str(e)}") from e
    
    # Should not reach here, but just in case
    raise FetchError(
        f"Exhausted all retry attempts for {url}. Last error: {str(last_exception)}"
    )


def fetch_with_backoff_bytes(
    url: str,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    timeout: float = 30.0,
    extra_retry_codes: Optional[list] = None
) -> bytes:
    """
    Fetch binary content from a URL with exponential backoff retry logic.
    
    This function is similar to fetch_with_backoff but returns raw bytes
    instead of decoding to string. Useful for downloading files, images,
    or other binary data.
    
    Args:
        url: The URL to fetch content from.
        max_retries: Maximum number of retry attempts (default: 5).
        base_delay: Initial delay in seconds between retries (default: 1.0).
        max_delay: Maximum delay cap in seconds (default: 60.0).
        timeout: Request timeout in seconds (default: 30.0).
        extra_retry_codes: Additional HTTP status codes to retry on.
        
    Returns:
        The fetched content as bytes.
        
    Raises:
        FetchError: If all retry attempts fail or a non-retryable error occurs.
        urllib.error.URLError: If the URL is invalid or unreachable.
        urllib.error.HTTPError: If an HTTP error occurs that is not retryable.
    """
    retry_codes = {429, 500, 502, 503, 504}
    if extra_retry_codes:
        retry_codes.update(extra_retry_codes)
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries + 1})")
            
            req = urllib.request.Request(url, headers={'User-Agent': 'llmXive-Research/1.0'})
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status_code = response.getcode()
                if status_code in retry_codes and attempt < max_retries:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(
                        f"HTTP {status_code} received. Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    continue
                
                if status_code != 200:
                    raise FetchError(
                        f"HTTP {status_code} for {url} - not retryable"
                    )
                
                return response.read()
                
        except (urllib.error.HTTPError, urllib.error.URLError, socket.timeout, 
               ConnectionResetError, TimeoutError) as e:
            last_exception = e
            
            if isinstance(e, urllib.error.HTTPError) and e.code in retry_codes:
                if attempt < max_retries:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(
                        f"HTTP {e.code} received. Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    continue
                else:
                    raise FetchError(
                        f"Failed after {max_retries + 1} attempts: HTTP {e.code} - {str(e)}"
                    ) from e
            
            elif isinstance(e, (urllib.error.URLError, socket.timeout, 
                               ConnectionResetError, TimeoutError)):
                if attempt < max_retries:
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(
                        f"Network error: {type(e).__name__}. Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    continue
                else:
                    raise FetchError(
                        f"Failed after {max_retries + 1} attempts: {type(e).__name__} - {str(e)}"
                    ) from e
            
            else:
                raise FetchError(f"Fatal error fetching {url}: {str(e)}") from e
                
        except Exception as e:
            raise FetchError(f"Unexpected error fetching {url}: {str(e)}") from e
    
    raise FetchError(
        f"Exhausted all retry attempts for {url}. Last error: {str(last_exception)}"
    )