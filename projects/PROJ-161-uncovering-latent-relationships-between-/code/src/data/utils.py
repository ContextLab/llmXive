import time
import logging
import urllib.request
import urllib.error
from typing import Callable, Any, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class FetchError(Exception):
    """Custom exception for data fetching failures after retries."""

    def __init__(self, message: str, last_exception: Optional[Exception] = None):
        super().__init__(message)
        self.last_exception = last_exception


def fetch_with_backoff(
    url: str,
    dest_path: Union[str, Path],
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    timeout: float = 30.0,
) -> Path:
    """
    Fetch a file from a URL with exponential backoff and jitter.

    Args:
        url: The URL to fetch from.
        dest_path: Local path to save the downloaded file.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds between retries.
        max_delay: Maximum delay in seconds between retries.
        timeout: Request timeout in seconds.

    Returns:
        Path to the successfully downloaded file.

    Raises:
        FetchError: If all retries fail.
    """
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    last_exception: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries + 1})...")
            urllib.request.urlretrieve(url, str(dest_path))
            logger.info(f"Successfully downloaded {url} to {dest_path}")
            return dest_path

        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            last_exception = e
            if attempt == max_retries:
                break

            # Exponential backoff with jitter
            delay = min(base_delay * (2 ** attempt), max_delay)
            jitter = delay * 0.1 * (hash(str(time.time())) % 10) / 10.0
            sleep_time = delay + jitter

            logger.warning(
                f"Fetch failed for {url}: {e}. "
                f"Retrying in {sleep_time:.2f}s (attempt {attempt + 1}/{max_retries})..."
            )
            time.sleep(sleep_time)

    raise FetchError(
        f"Failed to fetch {url} after {max_retries + 1} attempts.",
        last_exception=last_exception,
    )


def fetch_with_backoff_bytes(
    url: str,
    max_retries: int = 5,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    timeout: float = 30.0,
) -> bytes:
    """
    Fetch raw bytes from a URL with exponential backoff.

    Args:
        url: The URL to fetch from.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds between retries.
        max_delay: Maximum delay in seconds between retries.
        timeout: Request timeout in seconds.

    Returns:
        Raw bytes content of the response.

    Raises:
        FetchError: If all retries fail.
    """
    last_exception: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Fetching bytes from {url} (attempt {attempt + 1}/{max_retries + 1})...")
            req = urllib.request.Request(url, headers={"User-Agent": "llmXive/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                data = response.read()
            logger.info(f"Successfully fetched {len(data)} bytes from {url}")
            return data

        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            last_exception = e
            if attempt == max_retries:
                break

            delay = min(base_delay * (2 ** attempt), max_delay)
            jitter = delay * 0.1 * (hash(str(time.time())) % 10) / 10.0
            sleep_time = delay + jitter

            logger.warning(
                f"Fetch failed for {url}: {e}. "
                f"Retrying in {sleep_time:.2f}s (attempt {attempt + 1}/{max_retries})..."
            )
            time.sleep(sleep_time)

    raise FetchError(
        f"Failed to fetch bytes from {url} after {max_retries + 1} attempts.",
        last_exception=last_exception,
    )
