"""
Network utilities for robust data ingestion.
Provides error handling wrappers, retry logic, and URL validation.
"""
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Callable, TypeVar
from functools import wraps
import requests

from requests.exceptions import Timeout, HTTPError, RequestException, ConnectionError

# Define a custom exception for ingestion errors to ensure pipeline continuity
class IngestionError(Exception):
    """Custom exception for data ingestion failures."""
    pass

T = TypeVar('T')

def retry_request(
    func: Callable[..., T],
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    status_forcelist: Tuple[int, ...] = (429, 500, 502, 503, 504)
) -> Callable[..., T]:
    """
    Decorator to add retry logic to network requests.
    
    Args:
        func: The network request function to wrap.
        max_retries: Maximum number of retry attempts.
        backoff_factor: Factor to multiply sleep time by on each retry.
        status_forcelist: HTTP status codes that trigger a retry.
        
    Returns:
        Wrapped function with retry logic.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except (Timeout, ConnectionError) as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = backoff_factor * (2 ** attempt)
                    logging.warning(
                        f"Network error on {func.__name__} (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    logging.error(f"Network error on {func.__name__} after {max_retries + 1} attempts: {e}")
                    raise IngestionError(f"Failed to connect after {max_retries + 1} attempts: {e}")
            except HTTPError as e:
                if e.response.status_code in status_forcelist:
                    if attempt < max_retries:
                        wait_time = backoff_factor * (2 ** attempt)
                        logging.warning(
                            f"HTTP {e.response.status_code} on {func.__name__} (attempt {attempt + 1}/{max_retries + 1}). "
                            f"Retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logging.error(f"HTTP error {e.response.status_code} on {func.__name__} after {max_retries + 1} attempts.")
                        raise IngestionError(f"HTTP {e.response.status_code} after retries: {e}")
                else:
                    # 404 or other client errors that shouldn't be retried
                    logging.error(f"Client error {e.response.status_code} on {func.__name__}: {e}")
                    raise IngestionError(f"Client error {e.response.status_code}: {e}")
            except RequestException as e:
                # Catch-all for other request exceptions
                logging.error(f"Request error on {func.__name__}: {e}")
                raise IngestionError(f"Request failed: {e}")
        raise last_exception

    return wrapper

@retry_request
def fetch_url(url: str, timeout: int = 30) -> requests.Response:
    """
    Fetch a URL with retry logic and timeout handling.
    
    Args:
        url: The URL to fetch.
        timeout: Request timeout in seconds.
        
    Returns:
        The requests.Response object.
        
    Raises:
        IngestionError: If the request fails after retries.
    """
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response

def check_url_availability(url: str, timeout: int = 10) -> bool:
    """
    Check if a URL is accessible (HEAD request preferred, fallback to GET).
    
    Args:
        url: The URL to check.
        timeout: Request timeout in seconds.
        
    Returns:
        True if the URL returns a 2xx status code, False otherwise.
    """
    try:
        # Try HEAD first
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if 200 <= response.status_code < 300:
            return True
        # Fallback to GET if HEAD is not allowed
        if response.status_code == 405:
            response = requests.get(url, timeout=timeout, allow_redirects=True)
            return 200 <= response.status_code < 300
        return False
    except (Timeout, ConnectionError, RequestException):
        return False

@retry_request
def download_file_with_error_handling(
    url: str,
    destination: Path,
    chunk_size: int = 8192,
    timeout: int = 60
) -> Path:
    """
    Download a file from a URL with robust error handling.
    
    Args:
        url: The URL to download from.
        destination: The local path to save the file.
        chunk_size: Size of chunks to download.
        timeout: Request timeout in seconds.
        
    Returns:
        The destination Path if successful.
        
    Raises:
        IngestionError: If the download fails.
    """
    try:
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:  # Filter out keep-alive chunks
                    f.write(chunk)
        
        logging.info(f"Successfully downloaded {url} to {destination}")
        return destination
        
    except Timeout:
        raise IngestionError(f"Download timeout for {url}")
    except HTTPError as e:
        if e.response.status_code == 404:
            raise IngestionError(f"File not found (404) at {url}")
        elif e.response.status_code == 403:
            raise IngestionError(f"Access forbidden (403) at {url}")
        else:
            raise IngestionError(f"HTTP error {e.response.status_code} downloading {url}")
    except RequestException as e:
        raise IngestionError(f"Failed to download {url}: {e}")

def validate_dataset_url(url: str) -> Tuple[bool, str]:
    """
    Validate that a dataset URL is reachable and returns a valid response.
    
    Args:
        url: The URL to validate.
        
    Returns:
        A tuple (is_valid, message).
    """
    if not url:
        return False, "URL is empty"
    
    if not (url.startswith('http://') or url.startswith('https://')):
        return False, f"Invalid URL scheme: {url}"
    
    if not check_url_availability(url):
        return False, f"URL not accessible: {url}"
    
    return True, "URL is valid"

def safe_download_dataset(
    url: str,
    base_dir: Path,
    filename: Optional[str] = None
) -> Optional[Path]:
    """
    Safely download a dataset with comprehensive error handling.
    
    Args:
        url: The dataset URL.
        base_dir: The base directory to save the file.
        filename: Optional filename. If None, derived from URL.
        
    Returns:
        The Path to the downloaded file, or None if failed.
    """
    if not filename:
        filename = url.split('/')[-1]
        if not filename:
            filename = "dataset.zip"
    
    destination = base_dir / filename
    
    try:
        return download_file_with_error_handling(url, destination)
    except IngestionError as e:
        logging.error(f"Failed to download dataset {url}: {e}")
        return None

def safe_ingest_datasets(
    urls: list,
    base_dir: Path
) -> Dict[str, Any]:
    """
    Attempt to ingest multiple datasets with error handling.
    
    Args:
        urls: List of dataset URLs.
        base_dir: Base directory for downloads.
        
    Returns:
        Dictionary with 'successful' list of paths and 'failed' list of (url, error) tuples.
    """
    results = {
        'successful': [],
        'failed': []
    }
    
    for url in urls:
        try:
            valid, msg = validate_dataset_url(url)
            if not valid:
                results['failed'].append((url, f"Validation failed: {msg}"))
                continue
            
            downloaded_path = safe_download_dataset(url, base_dir)
            if downloaded_path:
                results['successful'].append(str(downloaded_path))
            else:
                results['failed'].append((url, "Download returned None"))
                
        except Exception as e:
            logging.exception(f"Unexpected error processing {url}")
            results['failed'].append((url, f"Unexpected error: {str(e)}"))
    
    return results