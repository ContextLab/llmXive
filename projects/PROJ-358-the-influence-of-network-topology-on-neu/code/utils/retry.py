"""
Retry utilities for network operations with exponential backoff.

This module provides robust error handling for network requests,
specifically designed to handle OpenNeuro API rate limits (429)
and transient connection failures.

Usage:
    from utils.retry import retry_request
    response = retry_request(url, method='GET', timeout=30)
"""

import logging
import time
from typing import Callable, Any, Optional
from functools import wraps

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

from utils.logger import get_logger

logger = get_logger(__name__)

# Configuration constants
MAX_RETRIES: int = 5
INITIAL_BACKOFF: float = 1.0  # seconds
MAX_BACKOFF: float = 60.0     # seconds
BACKOFF_MULTIPLIER: float = 2.0
STATUS_CODES_RETRY: tuple = (429, 500, 502, 503, 504)  # Rate limit and server errors


def calculate_backoff(attempt: int) -> float:
    """
    Calculate exponential backoff with jitter.
    
    Args:
        attempt: Current retry attempt (0-indexed)
        
    Returns:
        Backoff time in seconds
    """
    backoff = min(INITIAL_BACKOFF * (BACKOFF_MULTIPLIER ** attempt), MAX_BACKOFF)
    # Add jitter (±20%) to prevent thundering herd
    jitter = backoff * 0.2
    import random
    return backoff + random.uniform(-jitter, jitter)


def retry_request(
    url: str,
    method: str = "GET",
    timeout: int = 30,
    max_retries: int = MAX_RETRIES,
    stream: bool = False,
    **kwargs
) -> requests.Response:
    """
    Execute a HTTP request with exponential backoff retry logic.
    
    This function automatically handles:
    - Rate limiting (HTTP 429)
    - Server errors (5xx)
    - Connection timeouts and failures
    
    Args:
        url: Target URL
        method: HTTP method (GET, POST, etc.)
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        stream: Whether to stream the response (for large downloads)
        **kwargs: Additional arguments passed to requests.request()
        
    Returns:
        requests.Response object
        
    Raises:
        requests.RequestException: If all retries are exhausted
        ValueError: If the response status code indicates a client error (4xx)
    """
    last_exception: Optional[Exception] = None
    
    for attempt in range(max_retries + 1):
        try:
            logger.debug(f"Request attempt {attempt + 1}/{max_retries + 1}: {method} {url}")
            
            response = requests.request(
                method=method,
                url=url,
                timeout=timeout,
                stream=stream,
                **kwargs
            )
            
            # Handle successful responses
            if response.status_code < 400:
                return response
            
            # Handle client errors (4xx) - don't retry
            if 400 <= response.status_code < 500:
                if response.status_code == 429:
                    # Rate limit - respect Retry-After header if present
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        wait_time = float(retry_after)
                        logger.warning(f"Rate limited. Waiting {wait_time}s as requested by server.")
                        time.sleep(wait_time)
                        continue
                    else:
                        # Default retry behavior for 429 without Retry-After
                        if attempt < max_retries:
                            wait_time = calculate_backoff(attempt)
                            logger.warning(f"Rate limited (429). Waiting {wait_time:.2f}s before retry {attempt + 1}/{max_retries}.")
                            time.sleep(wait_time)
                            continue
                        else:
                            logger.error("Rate limit exhausted all retries.")
                            raise requests.HTTPError(f"Rate limit exceeded after {max_retries} retries: {url}")
                else:
                    # Other 4xx errors are not retried
                    raise requests.HTTPError(f"Client error {response.status_code}: {response.text[:200]}")
            
            # Handle server errors (5xx) - retry
            if response.status_code >= 500:
                if attempt < max_retries:
                    wait_time = calculate_backoff(attempt)
                    logger.warning(f"Server error {response.status_code}. Waiting {wait_time:.2f}s before retry {attempt + 1}/{max_retries}.")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Server error {response.status_code} after {max_retries} retries.")
                    raise requests.HTTPError(f"Server error after {max_retries} retries: {url}")
            
            # Unexpected status code
            raise requests.HTTPError(f"Unexpected status code {response.status_code}: {response.text[:200]}")
            
        except (Timeout, ConnectionError) as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = calculate_backoff(attempt)
                logger.warning(f"Connection error: {e}. Waiting {wait_time:.2f}s before retry {attempt + 1}/{max_retries}.")
                time.sleep(wait_time)
            else:
                logger.error(f"Connection error after {max_retries} retries: {e}")
                raise requests.ConnectionError(f"Connection failed after {max_retries} retries: {url}") from e
                
        except RequestException as e:
            last_exception = e
            logger.error(f"Request failed: {e}")
            raise
    
    # Should not reach here, but just in case
    raise last_exception or requests.RequestException("Unknown error in retry logic")


def retry_with_backoff(
    func: Callable[..., Any],
    max_retries: int = MAX_RETRIES,
    exceptions: tuple = (RequestException, Timeout, ConnectionError)
) -> Callable[..., Any]:
    """
    Decorator to add retry logic with exponential backoff to any function.
    
    Args:
        func: Function to decorate
        max_retries: Maximum retry attempts
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Decorated function with retry capability
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        last_exception: Optional[Exception] = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = calculate_backoff(attempt)
                    logger.warning(
                        f"Function {func.__name__} failed: {e}. "
                        f"Waiting {wait_time:.2f}s before retry {attempt + 1}/{max_retries}."
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(f"Function {func.__name__} failed after {max_retries} retries: {e}")
                    raise
        
        raise last_exception or Exception("Unknown error in retry decorator")
    
    return wrapper