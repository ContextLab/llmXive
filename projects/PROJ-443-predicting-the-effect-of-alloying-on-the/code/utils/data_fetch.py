"""
Data fetching utilities for HEA research pipeline.
Handles API retries, rate limiting, and raw data download logic.
"""
import os
import time
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Callable, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging to use project standard if available, otherwise basic
try:
    from utils.logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Constants
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 1.0
DEFAULT_TIMEOUT = 30  # seconds
RATE_LIMIT_SLEEP = 1.0  # seconds between requests to respect limits

class DataFetcher:
    """
    A robust data fetcher with retry logic, rate limiting, and error handling.
    Designed to work with REST APIs like OQMD and Materials Project.
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
            base_url: Base URL of the API
            api_key: Optional API key for authentication
            max_retries: Maximum number of retry attempts
            backoff_factor: Exponential backoff factor for retries
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.timeout = timeout
        self.session = self._create_session()
        self._last_request_time = 0

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry configuration."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session

    def _respect_rate_limit(self):
        """Respect API rate limits by sleeping if necessary."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < RATE_LIMIT_SLEEP:
            sleep_time = RATE_LIMIT_SLEEP - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers including authentication if available."""
        headers = {
            "Accept": "application/json",
            "User-Agent": "llmXive-HEA-Research-Agent/1.0"
        }
        
        if self.api_key:
            # Common API key header patterns
            # Try to detect from base_url or use generic approach
            if "materialsproject" in self.base_url.lower():
                headers["X-API-Key"] = self.api_key
            elif "oqmd" in self.base_url.lower():
                # OQMD often uses query params, but some endpoints use headers
                headers["Authorization"] = f"Bearer {self.api_key}"
            else:
                # Generic fallback
                headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers

    def fetch_json(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        post_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch JSON data from an API endpoint with retry logic.

        Args:
            endpoint: API endpoint path (relative to base_url)
            params: Query parameters for GET requests
            post_data: Data payload for POST requests

        Returns:
            Parsed JSON response or None if all retries fail
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        
        self._respect_rate_limit()
        
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"Fetching {url} (attempt {attempt + 1}/{self.max_retries + 1})")
                
                if post_data:
                    response = self.session.post(
                        url,
                        headers=headers,
                        json=post_data,
                        timeout=self.timeout
                    )
                else:
                    response = self.session.get(
                        url,
                        headers=headers,
                        params=params,
                        timeout=self.timeout
                    )
                
                # Handle rate limiting (429)
                if response.status_code == 429:
                    retry_after = response.headers.get('Retry-After', str(self.backoff_factor * (attempt + 1)))
                    sleep_time = float(retry_after)
                    logger.warning(f"Rate limited. Waiting {sleep_time}s before retry.")
                    time.sleep(sleep_time)
                    continue
                
                # Handle server errors
                if response.status_code >= 500:
                    if attempt < self.max_retries:
                        sleep_time = self.backoff_factor * (2 ** attempt)
                        logger.warning(f"Server error {response.status_code}. Retrying in {sleep_time}s...")
                        time.sleep(sleep_time)
                        continue
                    else:
                        logger.error(f"Server error {response.status_code} after {self.max_retries} retries")
                        return None
                
                # Handle client errors (non-retryable)
                if response.status_code >= 400:
                    logger.error(f"Client error {response.status_code}: {response.text[:200]}")
                    return None
                
                # Success
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.Timeout:
                logger.warning(f"Request timeout. Attempt {attempt + 1}/{self.max_retries + 1}")
                if attempt == self.max_retries:
                    logger.error("All retry attempts failed due to timeout")
                    return None
                time.sleep(self.backoff_factor * (2 ** attempt))
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                if attempt == self.max_retries:
                    return None
                time.sleep(self.backoff_factor * (2 ** attempt))
        
        return None

    def fetch_to_file(
        self,
        endpoint: str,
        output_path: str,
        params: Optional[Dict[str, Any]] = None,
        post_data: Optional[Dict[str, Any]] = None,
        chunk_size: int = 8192
    ) -> bool:
        """
        Fetch data and save directly to file (useful for large downloads).

        Args:
            endpoint: API endpoint path
            output_path: Path to save the downloaded file
            params: Query parameters for GET requests
            post_data: Data payload for POST requests
            chunk_size: Chunk size for streaming downloads

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        
        self._respect_rate_limit()
        
        try:
            logger.info(f"Downloading {url} to {output_path}")
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            if post_data:
                response = self.session.post(
                    url,
                    headers=headers,
                    json=post_data,
                    timeout=self.timeout,
                    stream=True
                )
            else:
                response = self.session.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=self.timeout,
                    stream=True
                )
            
            if response.status_code == 429:
                logger.error("Rate limited and unable to proceed with download")
                return False
            
            if response.status_code >= 400:
                logger.error(f"Download failed with status {response.status_code}")
                return False
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)
            
            logger.info(f"Successfully saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Download failed: {str(e)}")
            return False

    def fetch_paginated(
        self,
        endpoint: str,
        output_path: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        page_size: int = 100,
        max_pages: Optional[int] = None,
        pagination_key: str = "data",
        next_page_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch paginated data from an API.

        Args:
            endpoint: API endpoint path
            output_path: Optional path to save aggregated results as JSON
            params: Initial query parameters
            page_size: Number of items per page
            max_pages: Maximum number of pages to fetch (None for unlimited)
            pagination_key: Key in response containing the data items
            next_page_key: Key in response containing the next page URL (if applicable)

        Returns:
            List of all fetched data items
        """
        all_data = []
        current_params = params.copy() if params else {}
        current_params.setdefault('limit', page_size)
        current_params.setdefault('offset', 0)
        
        page = 0
        has_more = True
        
        while has_more:
            if max_pages is not None and page >= max_pages:
                logger.info(f"Reached max_pages limit ({max_pages})")
                break
            
            logger.info(f"Fetching page {page + 1}")
            response_data = self.fetch_json(endpoint, params=current_params)
            
            if response_data is None:
                logger.error(f"Failed to fetch page {page + 1}, stopping pagination")
                break
            
            # Extract data items
            items = response_data.get(pagination_key, [])
            all_data.extend(items)
            logger.info(f"Retrieved {len(items)} items (total: {len(all_data)})")
            
            # Check for more pages
            if next_page_key and next_page_key in response_data:
                if response_data[next_page_key]:
                    # Handle URL-based pagination
                    endpoint = response_data[next_page_key].replace(self.base_url + '/', '')
                    current_params = None
                else:
                    has_more = False
            elif len(items) < page_size:
                # Fewer items than page size means we're at the end
                has_more = False
            else:
                # Offset-based pagination
                current_params['offset'] = current_params.get('offset', 0) + page_size
                page += 1
            
            # Small delay between pages
            if has_more:
                time.sleep(0.5)
        
        # Save to file if requested
        if output_path:
            try:
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as f:
                    json.dump(all_data, f, indent=2)
                logger.info(f"Saved {len(all_data)} items to {output_path}")
            except Exception as e:
                logger.error(f"Failed to save data to {output_path}: {str(e)}")
        
        return all_data

def create_fetcher(
    service_name: str,
    config: Optional[Dict[str, Any]] = None
) -> DataFetcher:
    """
    Factory function to create a configured DataFetcher based on service name.

    Args:
        service_name: Name of the data service (e.g., 'oqmd', 'materials_project')
        config: Optional configuration dictionary

    Returns:
        Configured DataFetcher instance
    """
    config = config or {}
    
    # Default configurations for common services
    service_configs = {
        'oqmd': {
            'base_url': 'http://oqmd.org/api/v1',
            'timeout': 60,
            'max_retries': 5
        },
        'materials_project': {
            'base_url': 'https://api.materialsproject.org',
            'timeout': 30,
            'max_retries': 3
        },
        'nomad': {
            'base_url': 'https://nomad-lab.eu/prod/rae/api/v1',
            'timeout': 30,
            'max_retries': 3
        }
    }
    
    if service_name.lower() not in service_configs:
        logger.warning(f"Unknown service '{service_name}', using defaults")
        config['base_url'] = config.get('base_url', 'https://example.com/api')
    else:
        # Merge service defaults with provided config
        defaults = service_configs[service_name.lower()]
        config = {**defaults, **config}
    
    return DataFetcher(
        base_url=config['base_url'],
        api_key=config.get('api_key'),
        max_retries=config.get('max_retries', DEFAULT_MAX_RETRIES),
        backoff_factor=config.get('backoff_factor', DEFAULT_BACKOFF_FACTOR),
        timeout=config.get('timeout', DEFAULT_TIMEOUT)
    )