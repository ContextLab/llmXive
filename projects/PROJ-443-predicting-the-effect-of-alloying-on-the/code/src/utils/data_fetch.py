"""
Data Fetching Utilities for HEA Elastic Modulus Prediction.

This module provides robust API retry logic and raw data download capabilities
for fetching High-Entropy Alloy (HEA) data from external sources like OQMD
and Materials Project.
"""

import os
import time
import json
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List, Union
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils.logging_config import get_logger
from utils.seeds import get_seed

# Constants for retry configuration
MAX_RETRIES = 5
BACKOFF_FACTOR = 2.0
STATUS_FORCELIST = [429, 500, 502, 503, 504]

logger = get_logger(__name__)


def create_retry_session() -> requests.Session:
    """
    Create a requests Session with automatic retry logic for transient failures.

    Returns:
        requests.Session: Configured session with retry strategy.
    """
    session = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        read=MAX_RETRIES,
        connect=MAX_RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=STATUS_FORCELIST,
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def fetch_url_with_retry(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    output_path: Optional[Path] = None
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Fetch data from a URL with automatic retry logic and optional file saving.

    Args:
        url: The API endpoint URL.
        params: Query parameters for the request.
        headers: HTTP headers (e.g., API keys).
        timeout: Request timeout in seconds.
        output_path: If provided, save the raw response to this file path.

    Returns:
        The parsed JSON response (dict or list).

    Raises:
        requests.exceptions.RequestException: If all retries fail.
        ValueError: If the response is not valid JSON.
    """
    session = create_retry_session()
    logger.info(f"Fetching data from: {url}")
    if params:
        logger.debug(f"Query params: {params}")

    try:
        response = session.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()

        # Attempt to parse JSON
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response from {url}: {e}")
            raise ValueError(f"Invalid JSON response from {url}") from e

        # Save to file if requested
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Saved raw data to: {output_path}")

        return data

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data from {url} after retries: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        raise


def fetch_paginated_data(
    base_url: str,
    params: Dict[str, Any],
    key: str,
    max_pages: Optional[int] = None,
    page_size: int = 100,
    headers: Optional[Dict[str, str]] = None,
    output_path: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    Fetch paginated data from an API, aggregating results across pages.

    Args:
        base_url: The base API URL.
        params: Base query parameters.
        key: The JSON key containing the list of items in the response.
        max_pages: Maximum number of pages to fetch (None for unlimited).
        page_size: Number of items per page.
        headers: HTTP headers.
        output_path: If provided, save aggregated results to this file.

    Returns:
        A list of all fetched items.
    """
    session = create_retry_session()
    all_items = []
    page = 1
    session_params = params.copy()

    while True:
        if max_pages and page > max_pages:
            logger.info(f"Reached max pages limit ({max_pages})")
            break

        session_params.update({"page": page, "limit": page_size})
        logger.info(f"Fetching page {page}...")

        try:
            response = session.get(base_url, params=session_params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            if key not in data:
                logger.warning(f"Key '{key}' not found in response for page {page}. Stopping pagination.")
                break

            items = data[key]
            if not items:
                logger.info(f"No more items on page {page}. Stopping.")
                break

            all_items.extend(items)
            logger.info(f"Fetched {len(items)} items (Total: {len(all_items)})")

            # Check if we have more pages
            total_count = data.get("total", data.get("count", len(items)))
            if len(all_items) >= total_count:
                break

            page += 1

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching page {page}: {e}")
            raise

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_items, f, indent=2, default=str)
        logger.info(f"Saved aggregated data to: {output_path}")

    return all_items


def fetch_raw_data(
    source_name: str,
    query_params: Dict[str, Any],
    output_dir: Path,
    filename_suffix: str = ".json"
) -> Path:
    """
    Generic wrapper to fetch raw data from a source with standard logging and saving.

    Args:
        source_name: Name of the data source (e.g., 'OQMD', 'MaterialsProject').
        query_params: Parameters for the API request.
        output_dir: Directory to save the raw data.
        filename_suffix: Suffix for the output filename.

    Returns:
        Path to the saved file.
    """
    timestamp = int(time.time())
    filename = f"{source_name.lower()}_raw_{timestamp}{filename_suffix}"
    output_path = output_dir / filename

    # This is a generic wrapper; specific fetchers should implement the actual URL logic
    # or pass the URL directly if this function is specialized.
    # For now, we assume the caller provides the URL in params or this is a placeholder
    # for the specific fetchers (T014, T015) to call.
    raise NotImplementedError(
        "fetch_raw_data requires a specific URL implementation. "
        "Use fetch_url_with_retry or fetch_paginated_data directly with the source URL."
    )


class DataFetcher:
    """
    Base class for data fetchers with common retry and logging logic.
    """

    def __init__(self, source_name: str, base_url: str, api_key: Optional[str] = None):
        """
        Initialize the DataFetcher.

        Args:
            source_name: Human-readable name of the data source.
            base_url: The base URL for the API.
            api_key: Optional API key for authentication.
        """
        self.source_name = source_name
        self.base_url = base_url
        self.session = create_retry_session()
        self.headers = {}
        if api_key:
            # Common header patterns; subclasses can override
            if "materialsproject" in base_url.lower():
                self.headers["X-Api-Key"] = api_key
            else:
                self.headers["Authorization"] = f"Bearer {api_key}"

        self.logger = get_logger(f"fetcher.{source_name}")

    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform a GET request to the specified endpoint.

        Args:
            endpoint: API endpoint (relative to base_url).
            params: Query parameters.

        Returns:
            Parsed JSON response.
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        self.logger.info(f"GET {url}")
        return fetch_url_with_retry(url, params=params, headers=self.headers)

    def fetch_all(self, endpoint: str, params: Optional[Dict[str, Any]] = None, key: str = "results") -> List[Dict[str, Any]]:
        """
        Fetch all paginated results from an endpoint.

        Args:
            endpoint: API endpoint.
            params: Base query parameters.
            key: JSON key containing the list of items.

        Returns:
            List of all items.
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        self.logger.info(f"Fetching all pages from {url}")
        return fetch_paginated_data(url, params or {}, key, headers=self.headers)

def create_fetcher(source_name: str, base_url: str, api_key: Optional[str] = None) -> DataFetcher:
    """
    Factory function to create a DataFetcher instance.

    Args:
        source_name: Name of the source.
        base_url: Base URL.
        api_key: API key.

    Returns:
        A DataFetcher instance.
    """
    return DataFetcher(source_name, base_url, api_key)
