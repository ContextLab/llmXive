import time
import logging
from typing import Callable, Any, Optional, Union
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import shutil

logger = logging.getLogger(__name__)

class MaxRetriesError(Exception):
    """Raised when the maximum number of retries is exceeded."""
    pass

class DataFetchError(Exception):
    """Raised when a data fetch operation fails fundamentally."""
    pass

def exponential_backoff_request(
    url: str,
    method: str = "GET",
    max_retries: int = 5,
    base_delay: float = 2.0,
    max_delay: float = 60.0
) -> Optional[bytes]:
    """
    Perform an HTTP request with exponential backoff.
    
    Args:
        url: The URL to request.
        method: HTTP method (GET or POST).
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
        
    Returns:
        Response bytes if successful, None otherwise.
        
    Raises:
        MaxRetriesError: If all retries fail.
    """
    attempt = 0
    delay = base_delay
    
    while attempt < max_retries:
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries} to fetch {url}")
            req = Request(url, method=method)
            
            with urlopen(req, timeout=30) as response:
                if response.status == 200:
                    return response.read()
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    
        except (URLError, HTTPError, TimeoutError) as e:
            logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
            attempt += 1
            if attempt < max_retries:
                time.sleep(delay)
                delay = min(delay * 2, max_delay)
            continue
            
        except Exception as e:
            logger.error(f"Unexpected error during request: {e}")
            raise DataFetchError(f"Unexpected error: {e}")
            
    raise MaxRetriesError(f"Failed to fetch {url} after {max_retries} attempts")

def fetch_file_with_retry(url: str, dest_path: Union[str, Path]) -> Path:
    """
    Download a file from a URL with retry logic and progress logging.
    
    Args:
        url: The URL to download from.
        dest_path: Local path to save the file.
        
    Returns:
        Path object of the downloaded file.
        
    Raises:
        MaxRetriesError: If download fails after all retries.
        DataFetchError: If the download fails fundamentally.
    """
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Downloading {url} to {dest_path}")
    
    # Use the retry logic to get content
    content = exponential_backoff_request(url, max_retries=5)
    
    if content is None:
        raise DataFetchError(f"Failed to retrieve content from {url}")
        
    # Write to file
    try:
        with open(dest_path, 'wb') as f:
            f.write(content)
        logger.info(f"Downloaded {len(content)} bytes to {dest_path}")
    except IOError as e:
        raise DataFetchError(f"Failed to write file {dest_path}: {e}")
        
    return dest_path

def main() -> None:
    """Entry point for CLI testing."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Example usage
    try:
        # This is just a test of the module structure
        logger.info("Network module loaded successfully")
    except Exception as e:
        logger.error(f"Error in network module: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
