"""
API Client with rate limiting and retry logic.
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
    """Retrieve API key from environment variable."""
    return os.getenv("MATERIALS_PROJECT_API_KEY") or os.getenv("OQMD_API_KEY")

class RateLimitedSession(requests.Session):
    """Session with automatic retry and exponential backoff."""
    
    def __init__(self):
        super().__init__()
        retry = Retry(
            total=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.mount("http://", adapter)
        self.mount("https://", adapter)

def fetch_with_backoff(session: RateLimitedSession, url: str, params: Dict[str, Any] = None, headers: Dict[str, str] = None) -> requests.Response:
    """
    Fetch data with exponential backoff for 429 errors.
    """
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = session.get(url, params=params, headers=headers)
            if response.status_code == 429:
                wait_time = (2 ** attempt)
                logger.warning(f"Rate limit hit. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)
    
    raise RuntimeError("Max retries exceeded")
