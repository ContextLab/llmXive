"""
utils/api_client.py
--------------------
Thin wrapper around the OpenML REST API with exponential‑backoff retry
handling for HTTP 429 responses.

Provides:
- ``DataFetchError``: exception raised on irrecoverable request failures.
- ``get_openml_json``: low‑level GET request with back‑off.
- ``OpenMLClient``: small helper class (currently unused but kept for API compatibility).
- ``fetch_top_classification_datasets``: fetches the top *limit* most‑downloaded
  classification datasets from OpenML.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests

__all__ = [
    "DataFetchError",
    "get_openml_json",
    "OpenMLClient",
    "fetch_top_classification_datasets",
]

class DataFetchError(Exception):
    """Raised when a request to an external service fails irrecoverably."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code

def _exponential_backoff(attempt: int, initial_delay: float, max_delay: float) -> float:
    """Return the sleep time for a given retry attempt."""
    delay = initial_delay * (2 ** (attempt - 1))
    return min(delay, max_delay)

def get_openml_json(
    endpoint: str,
    *,
    params: Dict[str, Any] = None,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    timeout: float = 10.0,
    base_url: str = "https://www.openml.org/api/v1/json/",
) -> Dict[str, Any]:
    """
    Retrieve a JSON payload from the OpenML REST API.

    Parameters
    ----------
    endpoint:
        Path component after the base URL (e.g., ``datasets/list``).
    params:
        Dictionary of query parameters that will be URL‑encoded.
    max_retries, initial_delay, max_delay, timeout, base_url:
        Same semantics as in the original implementation.

    Returns
    -------
    dict
        Parsed JSON response.

    Raises
    ------
    DataFetchError
        If the request ultimately fails (non‑200 status or network error).
    """
    if params:
        query = "?" + urlencode(params)
    else:
        query = ""
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}{query}"
    attempt = 0

    while True:
        attempt += 1
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                try:
                    return response.json()
                except json.JSONDecodeError as exc:
                    raise DataFetchError(
                        f"Invalid JSON returned from {url}", response.status_code
                    ) from exc
            elif response.status_code == 429:
                if attempt > max_retries:
                    raise DataFetchError(
                        f"Rate limit exceeded after {max_retries} retries",
                        response.status_code,
                    )
                sleep_time = _exponential_backoff(attempt, initial_delay, max_delay)
                time.sleep(sleep_time)
                continue
            else:
                raise DataFetchError(
                    f"Unexpected status {response.status_code} from {url}",
                    response.status_code,
                )
        except requests.RequestException as exc:
            raise DataFetchError(f"Network error while contacting {url}") from exc

class OpenMLClient:
    """
    Minimal client wrapper for OpenML API calls.
    Currently only used internally by ``fetch_top_classification_datasets``.
    """

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 10.0,
        timeout: float = 10.0,
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.timeout = timeout

    def get(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        return get_openml_json(
            endpoint,
            params=params,
            max_retries=self.max_retries,
            initial_delay=self.initial_delay,
            max_delay=self.max_delay,
            timeout=self.timeout,
        )

def fetch_top_classification_datasets(limit: int = 50) -> List[Dict]:
    """
    Fetch the top *limit* most‑downloaded classification datasets from OpenML.

    The OpenML endpoint ``data/list`` supports sorting and filtering via query
    parameters. We request datasets sorted by ``download_count`` in descending
    order and filter to those whose ``default_target_attribute`` is present
    (a heuristic for classification tasks). The API returns a nested structure;
    we extract the list of dataset dictionaries.

    Returns
    -------
    List[Dict]
        List of dataset metadata dictionaries.
    """
    client = OpenMLClient()
    params = {
        "limit": limit,
        "sort": "download_count",
        "order": "desc",
        # The OpenML API does not have a direct ``task_type`` filter for
        # classification, but most classification datasets have a non‑empty
        # ``default_target_attribute``. We keep the request simple.
    }
    payload = client.get("data/list", params=params)

    # The JSON structure is ``{'data': {'dataset': [...]}}``; guard against
    # unexpected shapes.
    datasets = payload.get("data", {}).get("dataset", [])
    if not isinstance(datasets, list):
        raise DataFetchError("Unexpected payload structure from OpenML.")
    return datasets
