import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Callable, TypeVar
from functools import wraps
import requests
from requests.exceptions import RequestException, Timeout, HTTPError

logger = logging.getLogger(__name__)

class IngestionError(Exception):
    """Custom exception for ingestion errors."""
    pass

def retry_request(method: str, url: str, max_retries: int = 3, 
                  backoff_factor: float = 1.0, **kwargs) -> requests.Response:
    """
    Retry a request with exponential backoff.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: Target URL
        max_retries: Maximum number of retries
        backoff_factor: Factor for exponential backoff
        **kwargs: Additional arguments for requests
        
    Returns:
        Response object
        
    Raises:
        IngestionError: If all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.request(method, url, **kwargs)
            
            # Check for HTTP errors
            if response.status_code >= 400:
                if response.status_code == 404:
                    raise IngestionError(f"Resource not found: {url}")
                elif response.status_code == 403:
                    raise IngestionError(f"Access forbidden: {url}")
                else:
                    raise HTTPError(f"HTTP {response.status_code}: {response.text}")
            
            return response
            
        except (Timeout, RequestException) as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = backoff_factor * (2 ** attempt)
                logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries + 1}): {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"All retries failed for {url}")
                
    raise IngestionError(f"Failed to fetch {url} after {max_retries + 1} attempts") from last_exception

def fetch_url(url: str, timeout: int = 30) -> requests.Response:
    """Fetch a URL with basic error handling."""
    return retry_request("GET", url, timeout=timeout)

def download_file_with_error_handling(url: str, dest_path: Path) -> bool:
    """
    Download a file with error handling.
    
    Args:
        url: Source URL
        dest_path: Destination path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        response = retry_request("GET", url, stream=True, timeout=60)
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Downloaded {url} to {dest_path}")
        return True
        
    except IngestionError as e:
        logger.error(f"Ingestion error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading {url}: {e}")
        return False

def check_url_availability(url: str, timeout: int = 10) -> bool:
    """Check if a URL is available."""
    try:
        response = requests.head(url, timeout=timeout)
        return response.status_code < 400
    except Exception:
        return False

def validate_dataset_url(url: str) -> bool:
    """Validate that a URL points to a dataset."""
    # Basic validation: check if it's a valid URL and points to a file
    if not url.lower().startswith(('http://', 'https://')):
        return False
    
    # Check if it ends with .csv or is a known API endpoint
    if not (url.lower().endswith('.csv') or '/files/' in url):
        logger.warning(f"URL may not point to a dataset: {url}")
        
    return True

def safe_download_dataset(url: str, dest_path: Path) -> Optional[Path]:
    """Safely download a dataset, returning the path if successful."""
    if not validate_dataset_url(url):
        logger.error(f"Invalid dataset URL: {url}")
        return None
    
    if download_file_with_error_handling(url, dest_path):
        return dest_path
    return None

def safe_ingest_datasets(urls: List[str], dest_dir: Path) -> Tuple[List[Path], List[str]]:
    """
    Safely ingest multiple datasets.
    
    Args:
        urls: List of URLs
        dest_dir: Destination directory
        
    Returns:
        Tuple of (successful paths, failed URLs)
    """
    successful = []
    failed = []
    
    for i, url in enumerate(urls):
        filename = f"dataset_{i}.csv"
        dest_path = dest_dir / filename
        
        if safe_download_dataset(url, dest_path):
            successful.append(dest_path)
        else:
            failed.append(url)
            
    return successful, failed
