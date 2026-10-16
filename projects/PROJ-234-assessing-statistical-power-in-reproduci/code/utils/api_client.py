"""
Thin wrapper around the OpenML REST API with exponential‑backoff retry
for HTTP 429 (Too Many Requests).

Provides:
    fetch_top_classification_datasets(
        max_datasets: int = 50,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 10.0,
    ) -> list[dict]

The function returns a list of dataset metadata dictionaries as returned by
the OpenML API (keys include at least ``dataset_id``, ``name``,
``download_count``, ``publication_link``, ``task_id`` etc.).
"""

import json
import time
from typing import List, Dict, Any

import requests
from llmxive_toolkit import get_logger

log = get_logger(__name__)

class DataFetchError(RuntimeError):
    """Raised when a data fetch from OpenML fails after retries."""
    pass


def _request_with_backoff(
    url: str,
    params: Dict[str, Any],
    max_retries: int,
    initial_delay: float,
    max_delay: float,
) -> requests.Response:
    """Perform a GET request with exponential back‑off on HTTP 429."""
    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, params=params, timeout=20)
            if response.status_code == 429:
                # Too Many Requests – back‑off
                log.warning(
                    f"Received 429 from OpenML (attempt {attempt}/{max_retries}); "
                    f"sleeping {delay}s before retry."
                )
                raise requests.HTTPError("429 Too Many Requests")
            response.raise_for_status()
            return response
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            if attempt == max_retries:
                log.error(f"Failed to fetch {url} after {max_retries} attempts.")
                raise DataFetchError(str(e)) from e
            log.info(f"Retrying request to {url} (attempt {attempt}/{max_retries})")
            time.sleep(delay)
            delay = min(delay * 2, max_delay)
    # Should never reach here
    raise DataFetchError("Exhausted retries without success")


def fetch_top_classification_datasets(
    max_datasets: int = 50,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
) -> List[Dict[str, Any]]:
    """
    Retrieve the most‑downloaded classification datasets from OpenML.

    Parameters
    ----------
    max_datasets : int
        Upper bound on the number of datasets to return.
    max_retries : int
        Number of retry attempts for HTTP 429.
    initial_delay : float
        Initial back‑off delay in seconds.
    max_delay : float
        Maximum back‑off delay in seconds.

    Returns
    -------
    List[dict]
        List of dataset metadata dictionaries.
    """
    base_url = "https://www.openml.org/api/v1/json/data/list"
    params = {
        "type": "Classification",
        "sort": "download_count",
        "limit": max_datasets,
    }
    log.info(
        f"Fetching top {max_datasets} classification datasets from OpenML "
        f"with back‑off (max_retries={max_retries})"
    )
    response = _request_with_backoff(
        base_url, params, max_retries, initial_delay, max_delay
    )
    try:
        payload = response.json()
    except json.JSONDecodeError as e:
        raise DataFetchError("Invalid JSON response from OpenML") from e

    # The API returns a nested structure: {"data": {"dataset": [ ... ]}}
    datasets = payload.get("data", {}).get("dataset", [])
    if not isinstance(datasets, list):
        # In some edge cases a single dict is returned
        datasets = [datasets]

    log.info(f"Retrieved {len(datasets)} datasets from OpenML")
    return datasets
