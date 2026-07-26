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
    request_func: Optional[Callable] = None,
    max_retries: int = MAX_RETRIES,
    initial_delay: float = INITIAL_RETRY_DELAY,
    max_delay: float = MAX_RETRY_DELAY
) -> Any:
    """
    Perform a request with exponential backoff.
    Retries on URLError or HTTPError (5xx).
    """
    if request_func is None:
        def request_func(req):
            return urlopen(req, timeout=30)

    attempt = 0
    delay = initial_delay

    while attempt <= max_retries:
        try:
            req = Request(url)
            response = request_func(req)
            return response
        except (URLError, HTTPError) as e:
            attempt += 1
            if attempt > max_retries:
                logger.error(f"Max retries ({max_retries}) exceeded for {url}.")
                raise MaxRetriesError(f"Failed to fetch {url} after {max_retries} retries.") from e

            # Exponential backoff with jitter
            jitter = (delay * 0.1) * (hash(url) % 100) / 100.0
            sleep_time = min(delay + jitter, max_delay)
            logger.warning(f"Retry {attempt}/{max_retries} for {url} in {sleep_time:.2f}s due to {e}.")
            time.sleep(sleep_time)
            delay *= 2

def fetch_file_with_retry(url: str, dest_path: Union[str, Path]) -> Path:
    """
    Fetch a file from a URL with retry logic and save to dest_path.
    """
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    response = exponential_backoff_request(url)

    with open(dest, 'wb') as f:
        f.write(response.read())

    logger.info(f"Downloaded {url} to {dest}")
    return dest

def main() -> None:
    """CLI entry point for testing network utility."""
    import sys
    if len(sys.argv) < 3:
        print("Usage: python -m code.utils.network <url> <destination>")
        sys.exit(1)
    fetch_file_with_retry(sys.argv[1], sys.argv[2])

if __name__ == "__main__":
    main()
