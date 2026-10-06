"""
Data Fetch Module for HEA Project.

Handles API retries, session management, and raw data download logic.
Provides a robust interface for fetching data from external sources like OQMD and Materials Project.
"""
import os
import time
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List, Union
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import logging config from project utils
try:
    from src.utils.logging_config import get_logger
except ImportError:
    # Fallback for direct execution or different import structure
    import logging
    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(name)

logger = get_logger(__name__)

# Configuration constants
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 1.0
DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_USER_AGENT = "llmXive-HEA-Research-Agent/1.0"


def create_retry_session(
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    status_forcelist: Optional[List[int]] = None,
    user_agent: str = DEFAULT_USER_AGENT
) -> requests.Session:
    """
    Create a requests Session with automatic retry logic for transient failures.
    
    Args:
        max_retries: Maximum number of retry attempts.
        backoff_factor: Factor to multiply the wait time by for each retry.
        status_forcelist: List of HTTP status codes to force a retry on.
        user_agent: User-Agent string to send with requests.
        
    Returns:
        A configured requests.Session object.
    """
    if status_forcelist is None:
        status_forcelist = [429, 500, 502, 503, 504]
    
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    
    # Mount adapters to both http and https
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Set default headers
    session.headers.update({"User-Agent": user_agent})
    
    logger.debug(f"Created retry session with max_retries={max_retries}, backoff={backoff_factor}")
    return session


def fetch_url_with_retry(
    url: str,
    session: Optional[requests.Session] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR
) -> Dict[str, Any]:
    """
    Fetch data from a URL with automatic retry logic.
    
    Args:
        url: The URL to fetch.
        session: Optional pre-configured session. If None, creates a new one.
        params: Optional query parameters.
        timeout: Request timeout in seconds.
        max_retries: Maximum retry attempts.
        backoff_factor: Backoff factor for retries.
        
    Returns:
        Parsed JSON response as a dictionary.
        
    Raises:
        requests.exceptions.RequestException: If all retries fail.
        ValueError: If response is not valid JSON.
    """
    if session is None:
        session = create_retry_session(max_retries=max_retries, backoff_factor=backoff_factor)
    
    logger.info(f"Fetching URL: {url}")
    
    try:
        response = session.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        
        # Attempt to parse JSON
        try:
            data = response.json()
            logger.info(f"Successfully fetched and parsed JSON from {url}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from {url}: {e}")
            # Try to return raw text if JSON fails, wrapped in a dict
            return {"raw_text": response.text, "_parse_error": str(e)}
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed after retries for {url}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        raise


def fetch_paginated_data(
    base_url: str,
    session: Optional[requests.Session] = None,
    initial_params: Optional[Dict[str, Any]] = None,
    page_param: str = "page",
    per_page_param: str = "limit",
    per_page_size: int = 100,
    timeout: int = DEFAULT_TIMEOUT,
    max_pages: Optional[int] = None,
    data_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch paginated data from an API.
    
    Args:
        base_url: The base URL of the API.
        session: Optional pre-configured session.
        initial_params: Initial query parameters (excluding pagination).
        page_param: Name of the page parameter.
        per_page_param: Name of the items per page parameter.
        per_page_size: Number of items per page.
        timeout: Request timeout.
        max_pages: Maximum number of pages to fetch (None for unlimited).
        data_key: Key in response containing the data list. If None, assumes response is the list.
        
    Returns:
        A list of all items fetched across pages.
    """
    if session is None:
        session = create_retry_session()
        
    if initial_params is None:
        initial_params = {}
        
    all_data = []
    page = 1
    total_fetched = 0
    
    params = initial_params.copy()
    params[per_page_param] = per_page_size
    
    logger.info(f"Starting paginated fetch from {base_url}")
    
    while True:
        if max_pages and page > max_pages:
            logger.info(f"Reached max_pages limit ({max_pages})")
            break
            
        params[page_param] = page
        
        try:
            response = session.get(base_url, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            
            # Extract data list
            if data_key and isinstance(data, dict):
                items = data.get(data_key, [])
            elif isinstance(data, list):
                items = data
            else:
                logger.warning(f"Unexpected response structure at page {page}: {type(data)}")
                items = []
            
            if not items:
                logger.info(f"No more items found at page {page}. Stopping pagination.")
                break
                
            all_data.extend(items)
            total_fetched += len(items)
            logger.debug(f"Fetched page {page}: {len(items)} items (Total: {total_fetched})")
            
            # Check if we've reached the end (e.g., fewer items than requested)
            if len(items) < per_page_size:
                logger.info(f"Received fewer items than requested ({len(items)} < {per_page_size}). End of data.")
                break
                
            page += 1
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching page {page}: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error on page {page}: {e}")
            raise
            
    logger.info(f"Paginated fetch complete. Total items: {total_fetched}")
    return all_data


def fetch_raw_data(
    url: str,
    output_path: Union[str, Path],
    session: Optional[requests.Session] = None,
    timeout: int = DEFAULT_TIMEOUT
) -> Path:
    """
    Fetch raw data (binary or text) from a URL and save it to a file.
    
    Args:
        url: URL to fetch.
        output_path: Path to save the downloaded file.
        session: Optional pre-configured session.
        timeout: Request timeout.
        
    Returns:
        Path to the saved file.
        
    Raises:
        requests.exceptions.RequestException: If download fails.
        IOError: If file cannot be written.
    """
    if session is None:
        session = create_retry_session()
        
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading raw data from {url} to {output_path}")
    
    try:
        with session.get(url, timeout=timeout, stream=True) as r:
            r.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        
        logger.info(f"Successfully downloaded to {output_path}")
        return output_path
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        raise
    except IOError as e:
        logger.error(f"Failed to write to {output_path}: {e}")
        raise


class DataFetcher:
    """
    A class-based interface for fetching data with configurable retry and logging.
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        timeout: int = DEFAULT_TIMEOUT
    ):
        """
        Initialize the DataFetcher.
        
        Args:
            base_url: Base URL for the API.
            api_key: Optional API key for authentication.
            max_retries: Max retry attempts.
            backoff_factor: Backoff factor.
            timeout: Request timeout.
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout
        self.session = create_retry_session(
            max_retries=max_retries,
            backoff_factor=backoff_factor
        )
        
        if api_key:
            self.session.headers.update({"Authorization": f"Token {api_key}"})
        
        logger.debug(f"DataFetcher initialized for {self.base_url}")
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        GET request to an endpoint.
        
        Args:
            endpoint: API endpoint (relative to base_url).
            params: Query parameters.
            
        Returns:
            Parsed JSON response.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return fetch_url_with_retry(
            url,
            session=self.session,
            params=params,
            timeout=self.timeout,
            max_retries=self.max_retries,
            backoff_factor=self.backoff_factor
        )
    
    def fetch_all_paginated(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        page_param: str = "page",
        per_page_param: str = "limit",
        per_page_size: int = 100,
        max_pages: Optional[int] = None,
        data_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch all pages of paginated data.
        
        Args:
            endpoint: API endpoint.
            params: Initial query parameters.
            page_param: Page parameter name.
            per_page_param: Items per page parameter name.
            per_page_size: Items per page size.
            max_pages: Max pages to fetch.
            data_key: Key containing data list in response.
            
        Returns:
            List of all items.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        return fetch_paginated_data(
            url,
            session=self.session,
            initial_params=params,
            page_param=page_param,
            per_page_param=per_page_param,
            per_page_size=per_page_size,
            timeout=self.timeout,
            max_pages=max_pages,
            data_key=data_key
        )
    
    def download_raw(
        self,
        endpoint: str,
        output_path: Union[str, Path],
        params: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Download raw data to a file.
        
        Args:
            endpoint: API endpoint.
            output_path: Destination path.
            params: Query parameters.
            
        Returns:
            Path to saved file.
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        # Note: fetch_raw_data uses its own session logic, but we pass our session
        # to reuse connection pooling and auth headers.
        # We need to adapt fetch_raw_data to accept a session or create a new one here.
        # For now, we'll use the existing fetch_raw_data which creates its own session,
        # but we could refactor to use self.session.
        return fetch_raw_data(url, output_path, session=self.session, timeout=self.timeout)


def create_fetcher(
    name: str,
    base_url: str,
    api_key_env_var: Optional[str] = None,
    **kwargs
) -> DataFetcher:
    """
    Factory function to create a DataFetcher.
    
    Args:
        name: Name of the fetcher (for logging).
        base_url: Base URL.
        api_key_env_var: Environment variable name for API key.
        **kwargs: Additional arguments for DataFetcher.
        
    Returns:
        Configured DataFetcher instance.
    """
    api_key = None
    if api_key_env_var:
        api_key = os.getenv(api_key_env_var)
        if not api_key:
            logger.warning(f"API key environment variable {api_key_env_var} not set for {name}")
    
    logger.info(f"Creating DataFetcher: {name} -> {base_url}")
    return DataFetcher(
        base_url=base_url,
        api_key=api_key,
        **kwargs
    )


def main():
    """
    Example usage / CLI entry point for testing the fetcher.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Example: Test fetch with a known public endpoint (e.g., JSONPlaceholder)
    # Note: In real usage, this would be OQMD or MP
    test_url = "https://jsonplaceholder.typicode.com/todos/1"
    
    try:
        data = fetch_url_with_retry(test_url)
        print(f"Fetch successful: {data}")
    except Exception as e:
        print(f"Fetch failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
