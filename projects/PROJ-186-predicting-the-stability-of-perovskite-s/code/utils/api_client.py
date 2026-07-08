import time
import logging
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

def get_api_key() -> Optional[str]:
    """
    Retrieve the API key from environment variables.
    Returns None if not found.
    """
    import os
    return os.getenv("MATERIALS_PROJECT_API_KEY")

class RateLimitedSession(requests.Session):
    """
    A requests Session configured with retry logic for rate limiting.
    Uses urllib3's Retry to handle 429, 500, 502, 503, 504 errors with backoff.
    """
    def __init__(self):
        super().__init__()
        retry_strategy = Retry(
            total=5,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.mount("http://", adapter)
        self.mount("https://", adapter)

def fetch_with_backoff(
    url: str,
    max_retries: int = 3,
    base_delay: float = 1.0,
    session: Optional[requests.Session] = None
) -> Dict[str, Any]:
    """
    Fetch data from a URL with exponential backoff retry logic.
    Specifically targets 429 (Too Many Requests) errors.

    Args:
        url: The URL to fetch.
        max_retries: Maximum number of retry attempts.
        base_delay: Base delay in seconds for exponential backoff.
        session: Optional requests.Session to use. If None, a new one is created.

    Returns:
        The JSON response content as a dictionary.

    Raises:
        RequestException: If the request fails after all retries.
    """
    if session is None:
        session = requests.Session()

    attempt = 0
    while attempt <= max_retries:
        try:
            logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries + 1})")
            response = session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 429:
                attempt += 1
                if attempt > max_retries:
                    logger.error(f"Max retries ({max_retries}) exceeded for 429 error on {url}")
                    raise
                delay = base_delay * (2 ** (attempt - 1))
                logger.warning(f"Received 429. Retrying in {delay:.2f}s...")
                time.sleep(delay)
            else:
                # For non-429 errors, raise immediately or handle based on specific logic
                # For this task, we focus on 429, but let other errors bubble up or handle as needed
                logger.error(f"Request failed: {e}")
                raise
    raise Exception("Unexpected flow in fetch_with_backoff")