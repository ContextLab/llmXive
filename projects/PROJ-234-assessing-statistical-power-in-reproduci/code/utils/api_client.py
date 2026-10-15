"""
Utility module for interacting with the OpenML REST API with retry logic.
"""
import time
from typing import Any, Dict, Optional

import requests

class DataFetchError(Exception):
    """Custom exception for data fetch failures."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code

def _build_url(endpoint: str) -> str:
    """
    Construct the full URL for an OpenML endpoint.

    Parameters
    ----------
    endpoint : str
        The relative endpoint, e.g. ``datasets/list``.

    Returns
    -------
    str
        Full URL to query.
    """
    base = "https://www.openml.org/api/v1/"
    if not endpoint.startswith("/"):
        endpoint = endpoint.lstrip("/")
    return f"{base}{endpoint}"

def get_openml_json(
    endpoint: str,
    *,
    max_retries: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    """
    Retrieve JSON data from an OpenML endpoint using exponential‑backoff
    retries for HTTP 429 responses.

    Parameters
    ----------
    endpoint : str
        Relative OpenML endpoint (e.g. ``datasets/list``).
    max_retries : int, optional
        Maximum number of retry attempts after a 429 response.
    initial_delay : float, optional
        Initial back‑off delay in seconds.
    max_delay : float, optional
        Maximum back‑off delay in seconds.
    timeout : float, optional
        Request timeout in seconds.

    Returns
    -------
    dict
        Parsed JSON payload.

    Raises
    ------
    DataFetchError
        If the request fails with a non‑retryable status or the JSON
        cannot be decoded.
    """
    url = _build_url(endpoint)
    delay = initial_delay

    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, timeout=timeout)
        except Exception as exc:
            raise DataFetchError(f"Network error while fetching {url}: {exc}")

        # Successful response
        if 200 <= response.status_code < 300:
            try:
                return response.json()
            except Exception as exc:
                raise DataFetchError(
                    f"Failed to decode JSON from {url}: {exc}",
                    status_code=response.status_code,
                )

        # Rate‑limit handling
        if response.status_code == 429:
            if attempt == max_retries:
                raise DataFetchError(
                    f"Rate limit exceeded after {max_retries} retries for {url}",
                    status_code=429,
                )
            time.sleep(delay)
            delay = min(delay * 2, max_delay)
            continue

        # Any other non‑2xx status is non‑retryable
        raise DataFetchError(
            f"Request to {url} failed with status {response.status_code}",
            status_code=response.status_code,
        )
