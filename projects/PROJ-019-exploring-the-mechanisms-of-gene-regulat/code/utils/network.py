"""
Network utilities with retry logic and exponential backoff.
"""
import time
import logging
from typing import Callable, Any, Optional, Union
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse
from code.config import MAX_RETRIES, INITIAL_RETRY_DELAY, MAX_RETRY_DELAY

logger = logging.getLogger(__name__)

class MaxRetriesError(Exception):
    """Raised when the maximum number of retries is exceeded."""
    pass

def exponential_backoff_request(
    url: str,
    max_retries: int = MAX_RETRIES,
    initial_delay: float = INITIAL_RETRY_DELAY,
    max_delay: float = MAX_RETRY_DELAY,
    timeout: float = 30.0
) -> bytes:
    """
    Fetch a file from a URL with exponential backoff retry logic.
    
    Args:
        url: URL to fetch.
        max_retries: Maximum number of retry attempts.
        initial_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay between retries in seconds.
        timeout: Request timeout in seconds.
        
    Returns:
        Response content as bytes.
        
    Raises:
        MaxRetriesError: If all retries fail.
        URLError: If the URL is invalid or unreachable after retries.
    """
    last_exception = None
    delay = initial_delay

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempt {attempt}/{max_retries} to fetch {url}")
            request = Request(url)
            with urlopen(request, timeout=timeout) as response:
                return response.read()
        except (URLError, HTTPError) as e:
            last_exception = e
            logger.warning(
                f"Attempt {attempt} failed for {url}: {e}. "
                f"Retrying in {delay:.2f}s..."
            )
            if attempt < max_retries:
                time.sleep(delay)
                delay = min(delay * 2, max_delay)
            else:
                logger.error(f"Max retries ({max_retries}) exceeded for {url}")
    
    raise MaxRetriesError(
        f"Failed to fetch {url} after {max_retries} attempts. "
        f"Last error: {last_exception}"
    ) from last_exception

def fetch_file_with_retry(
    url: str,
    output_path: Optional[Union[str, Path]] = None,
    max_retries: int = MAX_RETRIES
) -> Path:
    """
    Fetch a file from a URL and save it to disk with retry logic.
    
    Args:
        url: URL to fetch.
        output_path: Path to save the file. If None, uses the URL filename.
        max_retries: Maximum number of retry attempts.
        
    Returns:
        Path to the saved file.
        
    Raises:
        MaxRetriesError: If all retries fail.
    """
    from code.config import TMP_DIR
    from pathlib import Path

    if output_path is None:
        parsed = urlparse(url)
        filename = Path(parsed.path).name
        if not filename:
            filename = "downloaded_file"
        output_path = TMP_DIR / filename
    else:
        output_path = Path(output_path)

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    content = exponential_backoff_request(url, max_retries=max_retries)
    
    with open(output_path, 'wb') as f:
        f.write(content)
    
    logger.info(f"Successfully downloaded {url} to {output_path}")
    return output_path

def main():
    """Main entry point for network test script."""
    # Example usage
    test_url = "https://www.google.com"
    try:
        fetch_file_with_retry(test_url, TMP_DIR / "test_download.html")
        print("Download successful")
    except MaxRetriesError as e:
        print(f"Download failed: {e}")
        return 1
    return 0

if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    sys.exit(main())
