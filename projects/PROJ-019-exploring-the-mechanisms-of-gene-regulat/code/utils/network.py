import time
import logging
from typing import Callable, Any, Optional, Union
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import os

logger = logging.getLogger(__name__)

class MaxRetriesError(Exception):
    """Raised when the maximum number of retry attempts is exceeded."""
    pass

class DataFetchError(Exception):
    """Raised when a data fetch operation fails and cannot be recovered."""
    pass

def exponential_backoff_request(
    func: Callable,
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    **kwargs
) -> Any:
    """
    Execute a function with exponential backoff retry logic.

    Args:
        func: The function to execute (e.g., a network request).
        *args: Positional arguments to pass to func.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds between retries.
        **kwargs: Keyword arguments to pass to func.

    Returns:
        The result of the function call.

    Raises:
        MaxRetriesError: If the function fails after max_retries attempts.
        Exception: Any other exception raised by func.
    """
    attempt = 0
    delay = base_delay

    while attempt <= max_retries:
        try:
            return func(*args, **kwargs)
        except (URLError, HTTPError, ConnectionError) as e:
            attempt += 1
            if attempt > max_retries:
                logger.error(f"Max retries ({max_retries}) exceeded. Last error: {e}")
                raise MaxRetriesError(f"Failed after {max_retries} retries: {e}")
            
            logger.warning(
                f"Attempt {attempt}/{max_retries} failed: {e}. Retrying in {delay:.2f}s..."
            )
            time.sleep(delay)
            delay = min(delay * 2, max_delay)
        except Exception as e:
            # Non-retryable errors (e.g., 404, 403) should not retry
            logger.error(f"Non-retryable error: {e}")
            raise

def fetch_file_with_retry(url: str, dest_path: Union[str, Path]) -> Path:
    """
    Download a file from a URL with exponential backoff retry logic.

    Args:
        url: The URL to download from.
        dest_path: Local path to save the file.

    Returns:
        Path object of the downloaded file.

    Raises:
        MaxRetriesError: If download fails after max retries.
        DataFetchError: If the URL is invalid or the server returns a permanent error.
    """
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    def _download():
        req = Request(url, headers={'User-Agent': 'llmXive/1.0'})
        with urlopen(req, timeout=30) as response:
            if response.status != 200:
                raise HTTPError(url, response.status, f"HTTP {response.status}", None, None)
            with open(dest_path, 'wb') as f:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    f.write(chunk)
        return dest_path

    try:
        return exponential_backoff_request(_download)
    except MaxRetriesError:
        raise
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        raise DataFetchError(f"Data fetch failed: {e}")

def main() -> None:
    """Entry point for CLI (demonstration)."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    # Example usage (not executed in production)
    # fetch_file_with_retry("https://www.encodeproject.org/files/ENCFF001XXX/download", "/tmp/test.bed")
    print("Network utility module loaded successfully.")

if __name__ == "__main__":
    main()
