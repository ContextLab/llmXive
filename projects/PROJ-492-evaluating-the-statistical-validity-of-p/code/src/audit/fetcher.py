"""HTML Fetcher module for A/B test audit pipeline.

Fetches HTML content from URLs with retry logic and timeout handling.
Saves fetched HTML files to data/raw/ directory.
"""

import hashlib
import time
from pathlib import Path
from typing import List, Tuple, Optional

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError

from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.utils.helpers import domain_from_url


# Configuration constants
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds between retries
USER_AGENT = "Mozilla/5.0 (compatible; ABTestAuditBot/1.0)"


def fetch_url_with_retry(
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
    logger: Optional[AuditLogger] = None
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Fetch HTML content from a URL with retry logic.

    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        logger: Optional logger instance

    Returns:
        Tuple of (success, html_content, error_message)
    """
    if logger is None:
        logger = get_default_logger()

    headers = {"User-Agent": USER_AGENT}

    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()
            return True, response.text, None
        except Timeout:
            error_msg = f"Timeout after {timeout}s on attempt {attempt + 1}"
            if attempt < max_retries:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            return False, None, error_msg
        except ConnectionError as e:
            error_msg = f"Connection error on attempt {attempt + 1}: {str(e)}"
            if attempt < max_retries:
                time.sleep(RETRY_DELAY * (attempt + 1))
                continue
            return False, None, error_msg
        except HTTPError as e:
            return False, None, f"HTTP error {e.response.status_code} on {url}"
        except RequestException as e:
            return False, None, f"Request failed: {str(e)}"

    return False, None, "Max retries exceeded"


def fetch_html_to_file(
    url: str,
    output_dir: Path,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
    logger: Optional[AuditLogger] = None
) -> Tuple[bool, Optional[Path], Optional[str]]:
    """
    Fetch HTML and save to a file in the output directory.

    Args:
        url: The URL to fetch
        output_dir: Directory to save the HTML file
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        logger: Optional logger instance

    Returns:
        Tuple of (success, filepath, error_message)
    """
    if logger is None:
        logger = get_default_logger()

    success, html_content, error_msg = fetch_url_with_retry(
        url, timeout=timeout, max_retries=max_retries, logger=logger
    )

    if not success or html_content is None:
        return False, None, error_msg

    # Create filename from domain and URL hash
    domain = domain_from_url(url)
    url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
    filename = f"{domain}_{url_hash}.html"
    filepath = output_dir / filename

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write HTML content to file
    filepath.write_text(html_content, encoding='utf-8')

    return True, filepath, None


def fetch_urls_batch(
    urls: List[str],
    output_dir: Path,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
    logger: Optional[AuditLogger] = None
) -> List[Tuple[str, bool, Optional[Path], Optional[str]]]:
    """
    Fetch multiple URLs and save HTML files.

    Args:
        urls: List of URLs to fetch
        output_dir: Directory to save HTML files
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        logger: Optional logger instance

    Returns:
        List of tuples: (url, success, filepath or None, error_message or None)
    """
    if logger is None:
        logger = get_default_logger()

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    results: List[Tuple[str, bool, Optional[Path], Optional[str]]] = []

    for url in urls:
        success, filepath, error_msg = fetch_html_to_file(
            url, output_dir, timeout=timeout, max_retries=max_retries, logger=logger
        )
        results.append((url, success, filepath, error_msg))

        if success:
            logger.info(f"Fetched {url} -> {filepath}")
        else:
            logger.error(f"Failed to fetch {url}: {error_msg}")

    return results


def ingest_and_fetch(
    input_csv: Path,
    output_dir: Path,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
    logger: Optional[AuditLogger] = None
) -> List[Tuple[str, bool, Optional[Path], Optional[str]]]:
    """
    Read URLs from CSV and fetch HTML for each.

    Args:
        input_csv: Path to CSV file with URLs (output of ingestor)
        output_dir: Directory to save HTML files
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        logger: Optional logger instance

    Returns:
        List of tuples: (url, success, filepath or None, error_message or None)
    """
    from code.src.audit.ingestor import read_urls_from_csv

    if logger is None:
        logger = get_default_logger()

    logger.info(f"Reading URLs from {input_csv}")
    urls = read_urls_from_csv(input_csv)

    if not urls:
        logger.warning("No URLs found in input CSV")
        return []

    logger.info(f"Fetched {len(urls)} URLs")
    return fetch_urls_batch(urls, output_dir, timeout=timeout, max_retries=max_retries, logger=logger)


def main() -> int:
    """
    Main entry point for HTML fetcher CLI.

    Reads URLs from data/urls_deduped.csv and saves HTML to data/raw/.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    from code.src.utils.logger import get_default_logger

    logger = get_default_logger()

    # Default paths
    input_csv = Path("data/urls_deduped.csv")
    output_dir = Path("data/raw")

    # Allow override via environment or arguments
    import sys
    if len(sys.argv) > 1:
        input_csv = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_dir = Path(sys.argv[2])

    logger.info(f"Starting HTML fetcher: {input_csv} -> {output_dir}")

    if not input_csv.exists():
        logger.error(f"Input file not found: {input_csv}")
        return 1

    results = ingest_and_fetch(input_csv, output_dir, logger=logger)

    success_count = sum(1 for _, success, _, _ in results if success)
    fail_count = len(results) - success_count

    logger.info(f"Fetch complete: {success_count} succeeded, {fail_count} failed")

    return 0 if fail_count == 0 else 1
