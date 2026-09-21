"""
Data Fetching Utilities for HEA Elastic Modulus Prediction.

This module provides robust utilities for fetching raw data from external APIs
(OQMD, Materials Project) with retry logic, pagination handling, and error management.
It is designed to work within the project's resource constraints (7GB RAM, CPU only).
"""
import os
import time
import json
import logging
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List, Union, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils.logging_config import get_logger
from utils.seeds import get_seed

# Initialize logger for this module
logger = get_logger(__name__)


def create_retry_session(
    total_retries: int = 5,
    backoff_factor: float = 1.0,
    status_forcelist: Optional[List[int]] = None,
    allowed_methods: Optional[List[str]] = None
) -> requests.Session:
    """
    Create a requests Session with automatic retry logic for transient failures.

    Args:
        total_retries: Total number of retries to allow.
        backoff_factor: A backoff factor to apply between attempts.
        status_forcelist: A list of status codes we should retry on.
        allowed_methods: A list of HTTP methods to retry on.

    Returns:
        A configured requests Session.
    """
    if status_forcelist is None:
        status_forcelist = [429, 500, 502, 503, 504]
    if allowed_methods is None:
        allowed_methods = ["HEAD", "GET", "OPTIONS"]

    retry_strategy = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=allowed_methods,
        raise_on_status=False
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    logger.info(f"Created retry session: {total_retries} retries, backoff={backoff_factor}")
    return session


def fetch_url_with_retry(
    url: str,
    session: Optional[requests.Session] = None,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
    max_retries: int = 5
) -> Union[Dict[str, Any], List[Dict[str, Any]], str]:
    """
    Fetch data from a URL with automatic retry logic.

    Args:
        url: The URL to fetch.
        session: Optional pre-configured session. If None, creates a new one.
        params: Query parameters.
        headers: Request headers.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts.

    Returns:
        The response data (parsed JSON if possible, otherwise text).

    Raises:
        RuntimeError: If all retries fail.
        ValueError: If the URL is invalid or the response is not successful.
    """
    if session is None:
        session = create_retry_session(total_retries=max_retries)

    logger.info(f"Fetching URL: {url}")
    if params:
        logger.debug(f"Parameters: {params}")

    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            response = session.get(url, params=params, headers=headers, timeout=timeout)
            
            if response.status_code == 200:
                # Try to parse as JSON
                try:
                    return response.json()
                except json.JSONDecodeError:
                    return response.text
            elif response.status_code == 429:
                # Rate limited - wait and retry
                wait_time = (2 ** attempt) * 2  # Exponential backoff
                logger.warning(f"Rate limited (429). Waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                time.sleep(wait_time)
                continue
            else:
                # Other error
                last_exception = RuntimeError(f"HTTP {response.status_code}: {response.text[:200]}")
                logger.error(f"HTTP Error {response.status_code}: {response.text[:200]}")
                break

        except requests.exceptions.Timeout as e:
            last_exception = e
            logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt == max_retries:
                break
            time.sleep(2 ** attempt)
            
        except requests.exceptions.RequestException as e:
            last_exception = e
            logger.warning(f"Request error on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt == max_retries:
                break
            time.sleep(2 ** attempt)

    # All retries exhausted
    if last_exception:
        logger.error(f"Failed to fetch {url} after {max_retries + 1} attempts")
        raise RuntimeError(f"Failed to fetch {url} after retries: {last_exception}")
    
    raise RuntimeError(f"Unexpected error fetching {url}")


def fetch_paginated_data(
    base_url: str,
    session: Optional[requests.Session] = None,
    params: Optional[Dict[str, Any]] = None,
    page_size: int = 100,
    max_pages: Optional[int] = None,
    response_key: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Fetch data from a paginated API endpoint.

    Args:
        base_url: The base URL of the API endpoint.
        session: Optional pre-configured session.
        params: Base query parameters.
        page_size: Number of items per page.
        max_pages: Maximum number of pages to fetch (None for unlimited).
        response_key: Key in the JSON response containing the data list.
        headers: Request headers.

    Returns:
        A list of all fetched items.

    Raises:
        RuntimeError: If fetching fails.
    """
    if session is None:
        session = create_retry_session()

    all_data = []
    page = 1
    total_fetched = 0

    # Ensure page size is in params
    fetch_params = params.copy() if params else {}
    fetch_params['limit'] = page_size
    fetch_params['offset'] = 0  # Using offset-based pagination

    while True:
        if max_pages and page > max_pages:
            logger.info(f"Reached max pages limit ({max_pages})")
            break

        fetch_params['offset'] = (page - 1) * page_size
        logger.info(f"Fetching page {page}...")

        try:
            response_data = fetch_url_with_retry(
                base_url, 
                session=session, 
                params=fetch_params, 
                headers=headers
            )

            if isinstance(response_data, dict):
                if response_key and response_key in response_data:
                    items = response_data[response_key]
                else:
                    # Assume the whole dict is the data or contains a list
                    items = response_data.get('results', response_data.get('data', [response_data]))
            elif isinstance(response_data, list):
                items = response_data
            else:
                logger.warning(f"Unexpected response format: {type(response_data)}")
                items = []

            if not items:
                logger.info(f"No more items on page {page}. Stopping pagination.")
                break

            all_data.extend(items)
            total_fetched += len(items)
            logger.info(f"Fetched {len(items)} items. Total: {total_fetched}")

            # Check if we got less than page_size, meaning last page
            if len(items) < page_size:
                logger.info(f"Last page reached (got {len(items)} < {page_size})")
                break

            page += 1
            
        except RuntimeError as e:
            logger.error(f"Failed to fetch page {page}: {e}")
            raise

    logger.info(f"Total items fetched: {len(all_data)}")
    return all_data


def fetch_raw_data(
    url: str,
    output_path: Optional[Union[str, Path]] = None,
    session: Optional[requests.Session] = None,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 60
) -> Path:
    """
    Fetch raw data from a URL and optionally save it to disk.

    Args:
        url: The URL to fetch.
        output_path: Optional path to save the file. If None, returns data in memory.
        session: Optional pre-configured session.
        params: Query parameters.
        headers: Request headers.
        timeout: Request timeout.

    Returns:
        Path to the saved file if output_path is provided, otherwise the data.

    Raises:
        RuntimeError: If fetch fails.
        ValueError: If output_path directory doesn't exist.
    """
    logger.info(f"Fetching raw data from: {url}")
    
    if session is None:
        session = create_retry_session()

    try:
        response = session.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Saved data to: {output_path} ({os.path.getsize(output_path)} bytes)")
            return output_path
        else:
            # Return content based on type
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                return response.json()
            else:
                return response.content

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch raw data: {e}")
        raise RuntimeError(f"Failed to fetch raw data: {e}")


class DataFetcher:
    """
    A class-based interface for fetching data from various sources.
    Encapsulates session management and common fetch logic.
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        max_retries: int = 5,
        timeout: int = 30
    ):
        """
        Initialize the DataFetcher.

        Args:
            base_url: The base URL of the API.
            api_key: Optional API key for authentication.
            max_retries: Maximum retry attempts.
            timeout: Request timeout.
        """
        self.base_url = base_url
        self.api_key = api_key
        self.max_retries = max_retries
        self.timeout = timeout
        self.session = create_retry_session(total_retries=max_retries)
        
        # Add API key to headers if provided
        if api_key:
            self.session.headers.update({'X-API-Key': api_key, 'Authorization': f'Token {api_key}'})

        logger.info(f"DataFetcher initialized for {base_url}")

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        save_to: Optional[Path] = None
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], Path]:
        """
        Fetch data from a specific endpoint.

        Args:
            endpoint: API endpoint (appended to base_url).
            params: Query parameters.
            save_to: Optional path to save the result.

        Returns:
            Fetched data or path to saved file.
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        if save_to:
            return fetch_raw_data(
                url, 
                output_path=save_to, 
                session=self.session, 
                params=params,
                timeout=self.timeout
            )
        else:
            return fetch_url_with_retry(
                url, 
                session=self.session, 
                params=params, 
                timeout=self.timeout
            )

    def paginate(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        page_size: int = 100,
        max_pages: Optional[int] = None,
        response_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch paginated data from an endpoint.

        Args:
            endpoint: API endpoint.
            params: Base query parameters.
            page_size: Items per page.
            max_pages: Max pages to fetch.
            response_key: Key containing data list.

        Returns:
            List of all fetched items.
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        return fetch_paginated_data(
            url,
            session=self.session,
            params=params,
            page_size=page_size,
            max_pages=max_pages,
            response_key=response_key,
            headers=self.session.headers
        )


def create_fetcher(
    source_name: str,
    base_url: str,
    api_key_env_var: Optional[str] = None
) -> DataFetcher:
    """
    Factory function to create a DataFetcher for a specific source.

    Args:
        source_name: Name of the data source (for logging).
        base_url: Base URL of the API.
        api_key_env_var: Environment variable name for the API key.

    Returns:
        Configured DataFetcher instance.
    """
    api_key = None
    if api_key_env_var:
        api_key = os.getenv(api_key_env_var)
        if not api_key:
            logger.warning(f"API key environment variable '{api_key_env_var}' not set for {source_name}")

    logger.info(f"Creating DataFetcher for {source_name} at {base_url}")
    return DataFetcher(base_url=base_url, api_key=api_key)