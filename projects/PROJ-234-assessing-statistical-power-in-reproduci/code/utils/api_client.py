"""
Utility module providing a thin wrapper around the OpenML REST API with
exponential‑backoff retry logic for HTTP 429 responses.

The public API surface required by the project consists of:
  - ``DataFetchError`` – custom exception raised on any fetch failure.
  - ``get_openml_json`` – low‑level fetcher used by unit tests.
  - ``OpenMLClient`` – small class encapsulating the base URL.
  - ``fetch_top_classification_datasets`` – convenience function used by the
    ingestion script (``code/01_ingest_openml.py``) to retrieve the top
    *limit* most‑downloaded classification datasets.
"""
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
    """Exception raised when a request to the OpenML API fails.

    Attributes
    ----------
    status_code: int
        HTTP status code returned by the server (if available).
    message: str
        Human‑readable description of the failure.
    """

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
        self.message = message

    def __str__(self) -> str:
        if self.status_code is not None:
            return f"[{self.status_code}] {self.message}"
        return self.message


def _request_with_backoff(
    url: str,
    *,
    max_retries: int,
    initial_delay: float,
    max_delay: float,
    timeout: float,
) -> requests.Response:
    """Perform a ``requests.get`` with exponential back‑off for 429 responses.

    Parameters
    ----------
    url: str
        Full URL to request.
    max_retries: int
        Maximum number of retry attempts after the initial request.
    initial_delay: float
        Seconds to wait before the first retry.
    max_delay: float
        Upper bound for the delay between retries.
    timeout: float
        ``requests`` timeout for the HTTP call.

    Returns
    -------
    requests.Response
        The successful response object.

    Raises
    ------
    DataFetchError
        If all retries are exhausted or a non‑retryable error occurs.
    """
    delay = initial_delay
    attempt = 0

    while True:
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 429:
                # Rate‑limit – decide whether we should retry
                if attempt >= max_retries:
                    raise DataFetchError(
                        f"Rate limited after {attempt} retries", status_code=429
                    )
                # Back‑off and retry
                time.sleep(delay)
                delay = min(delay * 2, max_delay)
                attempt += 1
                continue
            # Any other status code is considered final
            return response
        except requests.RequestException as exc:
            # Network‑level problems are not retryable for this wrapper
            raise DataFetchError(str(exc)) from exc

def get_openml_json(
    endpoint: str,
    *,
    max_retries: int = 5,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    timeout: float = 10.0,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Fetch a JSON payload from the OpenML REST API.

    Parameters
    ----------
    endpoint: str
        Relative OpenML endpoint, e.g. ``"datasets/list"``.
    max_retries, initial_delay, max_delay, timeout: see ``_request_with_backoff``.
    params: optional query parameters passed through ``urlencode``.

    Returns
    -------
    dict
        Parsed JSON response.

    Raises
    ------
    DataFetchError
        If the request fails, returns a non‑2xx status, or the payload cannot be
        decoded as JSON.
    """
    base_url = "https://www.openml.org/api/v1/json"
    if not endpoint.startswith("/"):
        endpoint = "/" + endpoint
    url = f"{base_url}{endpoint}"
    if params:
        url = f"{url}?{urlencode(params)}"

    response = _request_with_backoff(
        url,
        max_retries=max_retries,
        initial_delay=initial_delay,
        max_delay=max_delay,
        timeout=timeout,
    )

    if not response.ok:
        raise DataFetchError(
            f"HTTP error {response.status_code}", status_code=response.status_code
        )
    try:
        return response.json()
    except Exception as exc:
        raise DataFetchError("Invalid JSON response", status_code=response.status_code) from exc

class OpenMLClient:
    """Very small wrapper class used by the ingestion script.

    It stores the base URL and provides a ``get`` method that forwards to
    ``get_openml_json`` with the same retry semantics.
    """

    def __init__(
        self,
        max_retries: int = 5,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        timeout: float = 10.0,
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.timeout = timeout

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Delegate to :func:`get_openml_json` using the instance's settings."""
        return get_openml_json(
            endpoint,
            max_retries=self.max_retries,
            initial_delay=self.initial_delay,
            max_delay=self.max_delay,
            timeout=self.timeout,
            params=params,
        )

def fetch_top_classification_datasets(limit: int = 50) -> List[Dict[str, Any]]:
    """Return the *limit* most‑downloaded classification datasets from OpenML.

    The OpenML API does not provide a single “top‑N” endpoint, but the
    ``datasets/list`` endpoint can be filtered by ``type=classification`` and
    sorted by ``download_count``.  The request is performed via
    :func:`get_openml_json`, which already implements exponential back‑off.

    Parameters
    ----------
    limit: int
        Maximum number of datasets to return.

    Returns
    -------
    list[dict]
        List of dataset dictionaries as returned by the OpenML API.
    """
    # Parameters based on the OpenML documentation
    params = {
        "type": "classification",
        "sort": "download_count",
        "order": "desc",
        "size": str(limit),
    }
    payload = get_openml_json("datasets/list", params=params)
    # The JSON structure is ``{'data': {'dataset': [...]}}`` per OpenML spec.
    try:
        datasets = payload["data"]["dataset"]
        if not isinstance(datasets, list):
            # Some responses return a single dict when size==1
            datasets = [datasets]
    except KeyError as exc:
        raise DataFetchError("Unexpected OpenML response structure") from exc
    return datasets
