"""
Network utilities for robust data ingestion.

Provides error handling wrappers for network requests to ensure pipeline continuity
by handling timeouts, connection errors, and HTTP status codes gracefully.
"""
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Callable, TypeVar
from functools import wraps

import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError, RequestException

# Configure logger for this module
logger = logging.getLogger(__name__)

# Custom exception for pipeline continuity
class IngestionError(Exception):
    """Raised when dataset ingestion fails due to network or data issues."""
    pass

T = TypeVar('T')

def retry_request(
    func: Callable[..., T],
    max_retries: int = 3,
    base_delay: float = 1.0,
    backoff_factor: float = 2.0
) -> Callable[..., T]:
    """
    Decorator to add retry logic with exponential backoff to network functions.
    
    Args:
        func: The function to wrap (must accept url as first argument).
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds between retries.
        backoff_factor: Multiplier for delay after each retry.
        
    Returns:
        Wrapped function with retry logic.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        last_exception = None
        delay = base_delay

        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except (Timeout, ConnectionError) as e:
                last_exception = e
                if attempt == max_retries:
                    logger.error(f"Max retries ({max_retries}) exceeded for {args[0]}")
                    raise IngestionError(f"Network failure after {max_retries} retries: {str(e)}")
                
                logger.warning(f"Attempt {attempt + 1}/{max_retries + 1} failed for {args[0]}: {str(e)}. Retrying in {delay:.1f}s...")
                time.sleep(delay)
                delay *= backoff_factor
            except HTTPError as e:
                status_code = e.response.status_code if e.response else 0
                if status_code == 404:
                    logger.error(f"Resource not found (404) for {args[0]}")
                    raise IngestionError(f"Dataset not found: {args[0]} (HTTP 404)")
                elif status_code == 403:
                    logger.error(f"Forbidden access (403) for {args[0]}")
                    raise IngestionError(f"Access denied: {args[0]} (HTTP 403)")
                else:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(f"HTTP error {status_code} for {args[0]} after {max_retries} retries")
                        raise IngestionError(f"HTTP error {status_code} after retries: {str(e)}")
                    logger.warning(f"Attempt {attempt + 1}/{max_retries + 1} failed with HTTP {status_code}. Retrying...")
                    time.sleep(delay)
                    delay *= backoff_factor
            except RequestException as e:
                logger.error(f"Request failed for {args[0]}: {str(e)}")
                raise IngestionError(f"Request failed: {str(e)}")
        
        # Should not reach here, but just in case
        raise IngestionError(f"Unexpected failure in {func.__name__}")

    return wrapper

@retry_request
def fetch_url(url: str, timeout: int = 30, headers: Optional[Dict[str, str]] = None) -> requests.Response:
    """
    Fetch a URL with robust error handling and retry logic.
    
    Args:
        url: The URL to fetch.
        timeout: Request timeout in seconds.
        headers: Optional headers to include in the request.
        
    Returns:
        The requests.Response object if successful.
        
    Raises:
        IngestionError: If the request fails after retries or returns a critical error.
    """
    if headers is None:
        headers = {
            'User-Agent': 'llmXive-Research-Implementer/1.0'
        }
    
    response = requests.get(url, timeout=timeout, headers=headers)
    response.raise_for_status()
    return response

def download_file_with_error_handling(
    url: str,
    output_path: Path,
    timeout: int = 30,
    chunk_size: int = 8192
) -> bool:
    """
    Download a file from a URL with comprehensive error handling.
    
    Args:
        url: The URL to download from.
        output_path: Local path to save the file.
        timeout: Request timeout in seconds.
        chunk_size: Size of chunks to read when streaming.
        
    Returns:
        True if download was successful, False otherwise.
        
    Raises:
        IngestionError: If the download fails due to network issues or invalid URLs.
    """
    try:
        response = fetch_url(url, timeout=timeout)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:  # Filter out keep-alive chunks
                    f.write(chunk)
        
        logger.info(f"Successfully downloaded {url} to {output_path}")
        return True
        
    except IngestionError:
        # Re-raise our custom errors
        raise
    except Exception as e:
        logger.error(f"Unexpected error downloading {url}: {str(e)}")
        raise IngestionError(f"Failed to download {url}: {str(e)}")

def check_url_availability(url: str, timeout: int = 10) -> Tuple[bool, int, Optional[str]]:
    """
    Check if a URL is available and returns its status code.
    
    Args:
        url: The URL to check.
        timeout: Request timeout in seconds.
        
    Returns:
        Tuple of (is_available, status_code, error_message)
    """
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        # If HEAD fails, try GET
        if response.status_code == 405:
            response = requests.get(url, timeout=timeout, allow_redirects=True)
        
        is_available = response.status_code == 200
        return (is_available, response.status_code, None)
        
    except Timeout:
        return (False, 0, "Request timed out")
    except ConnectionError:
        return (False, 0, "Connection error")
    except RequestException as e:
        return (False, 0, str(e))

def validate_dataset_url(url: str) -> Tuple[bool, str]:
    """
    Validate that a dataset URL is accessible and points to a valid file.
    
    Args:
        url: The URL to validate.
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    is_available, status_code, error_msg = check_url_availability(url)
    
    if not is_available:
        if status_code == 404:
            return (False, f"Dataset not found (404): {url}")
        elif status_code == 403:
            return (False, f"Access denied (403): {url}")
        else:
            return (False, f"URL unavailable: {error_msg or 'Unknown error'}")
    
    # Check if it's a supported file type
    if not any(url.lower().endswith(ext) for ext in ['.csv', '.parquet', '.xlsx', '.json']):
        return (False, f"Unsupported file format: {url}")
    
    return (True, "OK")

# Compatibility wrapper for existing ingest.py functions
def safe_download_dataset(url: str, output_dir: Path, filename: Optional[str] = None) -> Optional[Path]:
    """
    Safe wrapper for download_dataset that handles network errors gracefully.
    
    Args:
        url: URL to download from.
        output_dir: Directory to save the file.
        filename: Optional filename (defaults to extracting from URL).
        
    Returns:
        Path to downloaded file, or None if download failed.
    """
    try:
        if filename is None:
            filename = url.split('/')[-1].split('?')[0]
        
        output_path = output_dir / filename
        download_file_with_error_handling(url, output_path)
        return output_path
    except IngestionError as e:
        logger.error(f"Failed to download {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in safe_download_dataset: {e}")
        return None

def safe_ingest_datasets(urls: list, output_dir: Path) -> list:
    """
    Safe wrapper for ingest_datasets that handles network errors gracefully.
    
    Args:
        urls: List of URLs to download.
        output_dir: Directory to save files.
        
    Returns:
        List of successfully downloaded file paths.
    """
    successful_downloads = []
    failed_urls = []
    
    for url in urls:
        try:
            result = safe_download_dataset(url, output_dir)
            if result:
                successful_downloads.append(result)
            else:
                failed_urls.append(url)
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            failed_urls.append(url)
    
    if failed_urls:
        logger.warning(f"Failed to download {len(failed_urls)} out of {len(urls)} datasets")
        for url in failed_urls:
            logger.warning(f"  - {url}")
    
    return successful_downloads
