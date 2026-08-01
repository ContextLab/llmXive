"""
code/utils/api_client.py

Provides a rate-limited HTTP client with exponential backoff for API calls.
"""
import time
import logging
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os

logger = logging.getLogger(__name__)


def get_api_key() -> Optional[str]:
    """Retrieves the API key from environment variables."""
    return os.getenv("MP_API_KEY")


class RateLimitedSession(requests.Session):
    """
    A requests Session with built-in retry logic and exponential backoff.
    Specifically handles 429 (Too Many Requests) and 5xx errors.
    """
    def __init__(self):
        super().__init__()
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.mount("https://", adapter)
        self.mount("http://", adapter)


def fetch_with_backoff(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> requests.Response:
    """
    Fetches a URL using a rate-limited session with exponential backoff.

    Args:
        url: The URL to fetch.
        params: Query parameters.
        headers: Request headers.

    Returns:
        The response object.

    Raises:
        requests.exceptions.RequestException: If the request fails after all retries.
    """
    session = RateLimitedSession()
    if headers:
        session.headers.update(headers)
    
    logger.info(f"Fetching {url} with params: {params}")
    
    response = session.get(url, params=params)
    
    # If we get a 429, the retry logic in the adapter should have handled it.
    # If we still get a 429 here, it means retries exhausted or it wasn't retried.
    if response.status_code == 429:
        logger.warning("Received 429 after retries. Rate limit may be strict.")
    
    return response
