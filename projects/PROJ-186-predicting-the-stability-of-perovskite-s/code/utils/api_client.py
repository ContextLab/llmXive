"""
API Client module for handling rate-limited requests with exponential backoff.

This module provides a session wrapper that automatically retries requests
when encountering HTTP 429 (Too Many Requests) errors, using exponential
backoff with jitter.
"""
import time
import logging
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Constants for retry logic
MAX_RETRIES = 5
BACKOFF_FACTOR = 2.0  # Exponential backoff multiplier
STATUS_FORCELIST = [429, 500, 502, 503, 504]  # 429 is the primary target

def get_api_key() -> str:
    """
    Retrieve the API key from environment variables.
    
    Returns:
        str: The API key string.
        
    Raises:
        ValueError: If the API key is not set in the environment.
    """
    api_key = os.getenv("MATERIALS_PROJECT_API_KEY")
    if not api_key:
        raise ValueError(
            "MATERIALS_PROJECT_API_KEY environment variable is not set. "
            "Please set it to your Materials Project API key."
        )
    return api_key

class RateLimitedSession(requests.Session):
    """
    A requests Session with automatic retry logic for rate-limited endpoints.
    
    This session uses urllib3's Retry logic to automatically retry failed
    requests, specifically targeting HTTP 429 (Too Many Requests) errors
    with exponential backoff.
    """
    
    def __init__(self, max_retries: int = MAX_RETRIES, backoff_factor: float = BACKOFF_FACTOR):
        """
        Initialize the RateLimitedSession.
        
        Args:
            max_retries: Maximum number of retry attempts.
            backoff_factor: Multiplier for exponential backoff.
        """
        super().__init__()
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=STATUS_FORCELIST,
            allowed_methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"],
            raise_on_status=False,  # We handle the status ourselves
        )
        
        # Mount the adapter to all HTTP(S) schemes
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.mount("http://", adapter)
        self.mount("https://", adapter)
        
        logger.info(f"RateLimitedSession initialized with max_retries={max_retries}, "
                    f"backoff_factor={backoff_factor}")

    def request(self, method, url, **kwargs):
        """
        Override request to add custom logging and retry handling.
        
        Args:
            method: HTTP method.
            url: Target URL.
            **kwargs: Additional arguments for requests.
            
        Returns:
            requests.Response: The response object.
        """
        start_time = time.time()
        attempt = 0
        last_status = None
        
        # Manually handle retries to log specific 429 events
        while attempt <= self.max_retries:
            try:
                response = super().request(method, url, **kwargs)
                last_status = response.status_code
                
                if response.status_code == 429:
                    attempt += 1
                    if attempt <= self.max_retries:
                        wait_time = self.backoff_factor ** attempt
                        # Add jitter (random 0-1s) to prevent thundering herd
                        jitter = time.time() % 1.0
                        total_wait = wait_time + jitter
                        
                        logger.warning(
                            f"Rate limit (429) hit on {url}. "
                            f"Attempt {attempt}/{self.max_retries}. "
                            f"Retrying in {total_wait:.2f}s."
                        )
                        time.sleep(total_wait)
                        continue
                    else:
                        logger.error(
                            f"Max retries ({self.max_retries}) exceeded for {url} "
                            f"after receiving 429."
                        )
                        return response
                
                # Success or non-retryable error
                elapsed = time.time() - start_time
                logger.debug(
                    f"Request {method} {url} completed in {elapsed:.2f}s "
                    f"with status {response.status_code}"
                )
                return response
                
            except requests.exceptions.ConnectionError as e:
                attempt += 1
                if attempt <= self.max_retries:
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(
                        f"Connection error on {url}. Attempt {attempt}/{self.max_retries}. "
                        f"Retrying in {wait_time}s. Error: {e}"
                    )
                    time.sleep(wait_time)
                    continue
                logger.error(f"Connection error exceeded retries for {url}: {e}")
                raise
            except requests.exceptions.Timeout as e:
                attempt += 1
                if attempt <= self.max_retries:
                    wait_time = self.backoff_factor ** attempt
                    logger.warning(
                        f"Timeout on {url}. Attempt {attempt}/{self.max_retries}. "
                        f"Retrying in {wait_time}s."
                    )
                    time.sleep(wait_time)
                    continue
                logger.error(f"Timeout exceeded retries for {url}: {e}")
                raise

def fetch_with_backoff(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    session: Optional[RateLimitedSession] = None
) -> requests.Response:
    """
    Fetch data from a URL with automatic exponential backoff for 429 errors.
    
    Args:
        url: The URL to fetch.
        params: Query parameters.
        headers: HTTP headers.
        timeout: Request timeout in seconds.
        session: Optional pre-configured session. If None, creates a new one.
        
    Returns:
        requests.Response: The response object.
        
    Raises:
        requests.exceptions.RequestException: If the request fails after all retries.
    """
    if session is None:
        session = RateLimitedSession()
    
    # Ensure API key is in headers if using Materials Project
    if headers is None:
        headers = {}
    
    # If no key in headers, try to get from env (for MP API)
    if "X-API-KEY" not in headers and "MATERIALS_PROJECT_API_KEY" in os.environ:
        headers["X-API-KEY"] = get_api_key()
        
    logger.info(f"Fetching {url} with backoff logic")
    
    response = session.get(url, params=params, headers=headers, timeout=timeout)
    
    # Log final status if it's an error
    if response.status_code >= 400:
        logger.error(
            f"Request to {url} failed with status {response.status_code} "
            f"after all retries."
        )
    
    return response