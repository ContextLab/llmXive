"""
Data Fetch Module: Handles API retries, session management, and raw data download logic.

This module provides robust HTTP fetching with exponential backoff,
pagination support, and raw data retrieval for the HEA project.
"""
import os
import time
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List, Union
from urllib.parse import urljoin, urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils.logging_config import get_logger

logger = get_logger(__name__)

# Default retry configuration
DEFAULT_MAX_RETRIES = 5
DEFAULT_BACKOFF_FACTOR = 1.0
DEFAULT_STATUS_FORCES = [429, 500, 502, 503, 504]
DEFAULT_TIMEOUT = 30  # seconds

# Constants for data paths
DATA_RAW_DIR = Path("data/raw")


def create_retry_session(
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    status_forcelist: List[int] = None,
    allowed_methods: List[str] = None,
) -> requests.Session:
    """
    Create a requests Session with automatic retry logic for transient errors.
    
    Args:
        max_retries: Maximum number of retry attempts.
        backoff_factor: Factor for exponential backoff (sleep = backoff_factor * (2 ** (retry - 1))).
        status_forcelist: List of HTTP status codes to retry on.
        allowed_methods: List of HTTP methods to retry (default: ['HEAD', 'GET', 'OPTIONS']).
        
    Returns:
        A configured requests.Session object.
        
    Raises:
        ValueError: If retry configuration is invalid.
    """
    if max_retries < 0:
        raise ValueError("max_retries must be non-negative")
    if backoff_factor < 0:
        raise ValueError("backoff_factor must be non-negative")
        
    session = requests.Session()
    
    retry = Retry(
        total=max_retries,
        read=max_retries,
        connect=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist or DEFAULT_STATUS_FORCES,
        allowed_methods=allowed_methods or ["HEAD", "GET", "OPTIONS"],
    )
    
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    logger.debug(f"Created retry session: max_retries={max_retries}, backoff={backoff_factor}")
    return session


def fetch_url_with_retry(
    url: str,
    session: Optional[requests.Session] = None,
    timeout: int = DEFAULT_TIMEOUT,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
) -> Union[Dict[str, Any], str, bytes]:
    """
    Fetch a URL with automatic retry logic and exponential backoff.
    
    Args:
        url: The URL to fetch.
        session: Optional pre-configured session. If None, a new one is created.
        timeout: Request timeout in seconds.
        params: Optional query parameters.
        headers: Optional request headers.
        max_retries: Maximum retry attempts (if creating a new session).
        backoff_factor: Backoff factor (if creating a new session).
        
    Returns:
        The response content as JSON (if Content-Type is application/json),
        text (if text/plain), or bytes (otherwise).
        
    Raises:
        requests.exceptions.RequestException: If all retries fail or a non-retryable error occurs.
        ValueError: If the URL is invalid.
    """
    if not url or not isinstance(url, str):
        raise ValueError("Invalid URL provided")
        
    logger.info(f"Fetching URL: {url}")
    
    # Create session if not provided
    if session is None:
        session = create_retry_session(max_retries, backoff_factor)
        
    try:
        response = session.get(url, params=params, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        content_type = response.headers.get("Content-Type", "").lower()
        
        if "application/json" in content_type:
            logger.debug("Parsing response as JSON")
            return response.json()
        elif "text/plain" in content_type or "text/csv" in content_type:
            logger.debug("Parsing response as text")
            return response.text
        else:
            logger.debug("Returning response as bytes")
            return response.content
            
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error fetching {url}: {e}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {url} after retries: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from {url}: {e}")
        raise


def fetch_paginated_data(
    base_url: str,
    endpoint: str,
    session: Optional[requests.Session] = None,
    timeout: int = DEFAULT_TIMEOUT,
    initial_params: Optional[Dict[str, Any]] = None,
    page_size: int = 100,
    max_pages: Optional[int] = None,
    response_key: str = "results",
    next_key: str = "next",
) -> List[Dict[str, Any]]:
    """
    Fetch paginated data from an API endpoint, aggregating all pages.
    
    Args:
        base_url: Base URL of the API.
        endpoint: API endpoint path (appended to base_url).
        session: Optional pre-configured session.
        timeout: Request timeout.
        initial_params: Initial query parameters (page will be added).
        page_size: Number of items per page.
        max_pages: Maximum number of pages to fetch (None for unlimited).
        response_key: Key in JSON response containing the data list.
        next_key: Key in JSON response containing the next page URL.
        
    Returns:
        A list of all aggregated data items.
        
    Raises:
        requests.exceptions.RequestException: If a request fails.
        ValueError: If the response format is invalid.
    """
    if not base_url or not endpoint:
        raise ValueError("base_url and endpoint must be provided")
        
    if session is None:
        session = create_retry_session()
        
    all_data = []
    page_count = 0
    
    # Build initial URL and params
    url = urljoin(base_url, endpoint)
    params = initial_params.copy() if initial_params else {}
    params["limit"] = page_size
    
    logger.info(f"Starting paginated fetch from {url}")
    
    while True:
        if max_pages and page_count >= max_pages:
            logger.info(f"Reached max_pages limit ({max_pages})")
            break
            
        try:
            logger.debug(f"Fetching page {page_count + 1}")
            response = fetch_url_with_retry(url, session=session, timeout=timeout, params=params)
            
            if not isinstance(response, dict):
                raise ValueError(f"Expected JSON dict response, got {type(response)}")
                
            if response_key not in response:
                raise ValueError(f"Response missing expected key '{response_key}'")
                
            page_data = response[response_key]
            all_data.extend(page_data)
            page_count += 1
            
            logger.info(f"Page {page_count}: retrieved {len(page_data)} items (total: {len(all_data)})")
            
            # Check for next page
            if next_key in response and response[next_key]:
                url = response[next_key]
                params = {}  # Next URL usually includes all params
                # Small delay to be polite to the API
                time.sleep(0.5)
            else:
                logger.info("No more pages found")
                break
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch page {page_count + 1}: {e}")
            raise
            
    logger.info(f"Completed paginated fetch: {len(all_data)} total items")
    return all_data


def fetch_raw_data(
    url: str,
    output_path: Optional[Union[str, Path]] = None,
    session: Optional[requests.Session] = None,
    timeout: int = DEFAULT_TIMEOUT,
    chunk_size: int = 8192,
) -> Path:
    """
    Fetch a large file from a URL and save it to disk as raw data.
    
    Args:
        url: URL of the file to download.
        output_path: Optional output path. If None, uses data/raw/<filename>.
        session: Optional pre-configured session.
        timeout: Request timeout.
        chunk_size: Chunk size for streaming download.
        
    Returns:
        Path to the downloaded file.
        
    Raises:
        requests.exceptions.RequestException: If download fails.
        ValueError: If output path cannot be determined.
    """
    if not url:
        raise ValueError("URL must be provided")
        
    # Determine output path
    if output_path is None:
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        if not filename:
            filename = "downloaded_data"
        DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        output_path = DATA_RAW_DIR / filename
    else:
        output_path = Path(output_path)
        
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading {url} to {output_path}")
    
    if session is None:
        session = create_retry_session()
        
    try:
        with session.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            with open(output_path, "wb") as f:
                downloaded = 0
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:  # filter out keep-alive chunks
                        f.write(chunk)
                        downloaded += len(chunk)
                        if downloaded % (1024 * 1024) < chunk_size:  # Log every ~1MB
                            logger.debug(f"Downloaded {downloaded / (1024*1024):.1f} MB")
                            
        logger.info(f"Successfully downloaded {output_path} ({output_path.stat().st_size} bytes)")
        return output_path
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        # Clean up partial file if it exists
        if output_path.exists():
            output_path.unlink()
        raise


class DataFetcher:
    """
    A reusable class for fetching data with configuration and retry logic.
    
    Attributes:
        base_url: Base URL for the API.
        session: Configured requests session with retry logic.
        timeout: Default timeout for requests.
        headers: Default headers for requests.
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    ):
        """
        Initialize the DataFetcher.
        
        Args:
            base_url: Base URL of the API.
            api_key: Optional API key for authentication.
            timeout: Default request timeout.
            max_retries: Maximum retry attempts.
            backoff_factor: Backoff factor for retries.
        """
        if not base_url:
            raise ValueError("base_url is required")
            
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = create_retry_session(max_retries, backoff_factor)
        
        # Set up default headers
        self.headers = {
            "Accept": "application/json",
            "User-Agent": "HEA-Research-Pipeline/1.0",
        }
        
        if api_key:
            # Common patterns for API key headers
            # Try to detect based on base_url or default to 'Authorization'
            if "materialsproject" in base_url.lower():
                self.headers["X-Api-Key"] = api_key
            else:
                self.headers["Authorization"] = f"Bearer {api_key}"
                
        logger.info(f"Initialized DataFetcher for {self.base_url}")
        
    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Union[Dict[str, Any], str, bytes]:
        """
        Perform a GET request to the specified endpoint.
        
        Args:
            endpoint: API endpoint path.
            params: Query parameters.
            headers: Additional headers.
            
        Returns:
            Response content.
        """
        url = urljoin(self.base_url, endpoint)
        merged_headers = {**self.headers, **(headers or {})}
        return fetch_url_with_retry(
            url,
            session=self.session,
            timeout=self.timeout,
            params=params,
            headers=merged_headers,
        )
        
    def fetch_all(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        page_size: int = 100,
        max_pages: Optional[int] = None,
        response_key: str = "results",
        next_key: str = "next",
    ) -> List[Dict[str, Any]]:
        """
        Fetch all paginated data from an endpoint.
        
        Args:
            endpoint: API endpoint path.
            params: Initial query parameters.
            page_size: Items per page.
            max_pages: Max pages to fetch.
            response_key: Key containing data list.
            next_key: Key containing next URL.
            
        Returns:
            List of all data items.
        """
        merged_params = {**(params or {}), "limit": page_size}
        return fetch_paginated_data(
            self.base_url,
            endpoint,
            session=self.session,
            timeout=self.timeout,
            initial_params=merged_params,
            page_size=page_size,
            max_pages=max_pages,
            response_key=response_key,
            next_key=next_key,
        )
        
    def download_file(
        self,
        url_or_endpoint: str,
        output_path: Optional[Union[str, Path]] = None,
    ) -> Path:
        """
        Download a file from a URL or endpoint.
        
        Args:
            url_or_endpoint: Full URL or endpoint path (if relative to base_url).
            output_path: Optional output path.
            
        Returns:
            Path to the downloaded file.
        """
        if not url_or_endpoint.startswith(("http://", "https://")):
            url = urljoin(self.base_url, url_or_endpoint)
        else:
            url = url_or_endpoint
            
        return fetch_raw_data(url, output_path, session=self.session, timeout=self.timeout)


def create_fetcher(
    service_name: str,
    base_url: str,
    api_key_env: Optional[str] = None,
    **kwargs
) -> DataFetcher:
    """
    Factory function to create a DataFetcher with environment-based API key.
    
    Args:
        service_name: Name of the service (for logging).
        base_url: Base URL of the API.
        api_key_env: Name of the environment variable containing the API key.
        **kwargs: Additional arguments for DataFetcher.
        
    Returns:
        Configured DataFetcher instance.
        
    Raises:
        ValueError: If API key is required but not found.
    """
    api_key = None
    if api_key_env:
        api_key = os.environ.get(api_key_env)
        if not api_key:
            logger.warning(f"API key environment variable '{api_key_env}' not set for {service_name}")
            # Don't raise here, let the fetcher handle it if auth is needed
            
    logger.info(f"Creating {service_name} fetcher at {base_url}")
    return DataFetcher(base_url, api_key=api_key, **kwargs)
