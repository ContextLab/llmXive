"""
HTML Fetcher Module for A/B Test Audit Pipeline.

This module handles fetching HTML content from URLs with retry logic,
timeouts, and saving to disk for subsequent extraction steps.
"""

import hashlib
import time
import logging
from pathlib import Path
from typing import List, Tuple, Optional

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError, HTTPError

from code.src.utils.logger import get_default_logger, AuditLogger
from code.src.utils.helpers import domain_from_url
from code.src.config import SEED

# Configure logging
logger = get_default_logger("fetcher")

# Constants
DEFAULT_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds
USER_AGENT = "llmXive-AuditBot/1.0"

def fetch_url_with_retry(
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
    retry_delay: float = RETRY_DELAY
) -> Tuple[Optional[str], Optional[Exception]]:
    """
    Fetch HTML content from a URL with retry logic.

    Args:
        url: The URL to fetch.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts.
        retry_delay: Delay between retries in seconds.

    Returns:
        A tuple of (html_content, error).
        If successful, html_content is the string content and error is None.
        If failed, html_content is None and error is the exception.
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Fetching URL (attempt {attempt + 1}/{max_retries + 1}): {url}")
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            logger.info(f"Successfully fetched URL: {url}, status: {response.status_code}")
            return response.text, None

        except Timeout as e:
            last_exception = e
            logger.warning(f"Timeout fetching {url} (attempt {attempt + 1}): {e}")

        except HTTPError as e:
            # If it's a 404 or similar permanent error, don't retry
            if e.response is not None and e.response.status_code in (400, 401, 403, 404, 410):
                logger.error(f"HTTP error {e.response.status_code} fetching {url}: {e}")
                return None, e
            last_exception = e
            logger.warning(f"HTTP error fetching {url} (attempt {attempt + 1}): {e}")

        except ConnectionError as e:
            last_exception = e
            logger.warning(f"Connection error fetching {url} (attempt {attempt + 1}): {e}")

        except RequestException as e:
            last_exception = e
            logger.warning(f"Request error fetching {url} (attempt {attempt + 1}): {e}")

        if attempt < max_retries:
            logger.info(f"Retrying in {retry_delay}s...")
            time.sleep(retry_delay)

    logger.error(f"Failed to fetch URL after {max_retries + 1} attempts: {url}")
    return None, last_exception

def fetch_html_to_file(
    url: str,
    output_dir: Path,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES
) -> Tuple[Optional[Path], Optional[Exception]]:
    """
    Fetch HTML content and save it to a file.

    Args:
        url: The URL to fetch.
        output_dir: Directory to save the HTML file.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts.

    Returns:
        A tuple of (file_path, error).
        If successful, file_path is the Path to the saved file and error is None.
        If failed, file_path is None and error is the exception.
    """
    html_content, error = fetch_url_with_retry(url, timeout, max_retries)

    if error is not None:
        return None, error

    if html_content is None:
        return None, Exception("No content received")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename based on URL hash to avoid collisions
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:12]
    domain = domain_from_url(url)
    filename = f"{domain}_{url_hash}.html"
    file_path = output_dir / filename

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"Saved HTML to: {file_path}")
        return file_path, None
    except IOError as e:
        logger.error(f"Failed to write file {file_path}: {e}")
        return None, e

def fetch_urls_batch(
    urls: List[str],
    output_dir: Path,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES
) -> List[Tuple[str, Optional[Path], Optional[Exception]]]:
    """
    Fetch multiple URLs and save them to files.

    Args:
        urls: List of URLs to fetch.
        output_dir: Directory to save HTML files.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts.

    Returns:
        List of tuples: (url, file_path_or_none, error_or_none)
    """
    results = []
    for url in urls:
        file_path, error = fetch_html_to_file(url, output_dir, timeout, max_retries)
        results.append((url, file_path, error))

        # Log progress
        if error is None:
            logger.info(f"SUCCESS: {url} -> {file_path}")
        else:
            logger.error(f"FAILED: {url} -> {error}")

    return results

def ingest_and_fetch(
    input_csv_path: Path,
    output_dir: Path,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES
) -> List[Tuple[str, Optional[Path], Optional[Exception]]]:
    """
    Read URLs from a CSV file and fetch them.

    Args:
        input_csv_path: Path to CSV file containing URLs (one per column or row).
        output_dir: Directory to save HTML files.
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts.

    Returns:
        List of tuples: (url, file_path_or_none, error_or_none)
    """
    # Read URLs from CSV
    # Expected format: either a single column 'url' or just plain URLs
    urls = []
    try:
        import csv
        with open(input_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if 'url' in reader.fieldnames:
                urls = [row['url'] for row in reader if row.get('url')]
            else:
                # Fallback: assume first column is URL
                f.seek(0)
                reader = csv.reader(f)
                for row in reader:
                    if row:
                        urls.append(row[0])
    except Exception as e:
        logger.error(f"Failed to read URLs from {input_csv_path}: {e}")
        return []

    logger.info(f"Found {len(urls)} URLs to fetch")
    return fetch_urls_batch(urls, output_dir, timeout, max_retries)

def main():
    """
    Main entry point for fetching HTML files.

    Usage:
        python -m code.src.audit.fetcher --input data/raw_urls.csv --output data/raw
    """
    import argparse

    parser = argparse.ArgumentParser(description="Fetch HTML content from URLs")
    parser.add_argument("--input", type=Path, required=True, help="Path to CSV with URLs")
    parser.add_argument("--output", type=Path, required=True, help="Output directory for HTML files")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help="Request timeout in seconds")
    parser.add_argument("--retries", type=int, default=MAX_RETRIES, help="Maximum retry attempts")

    args = parser.parse_args()

    logger.info(f"Starting fetcher: input={args.input}, output={args.output}")

    results = ingest_and_fetch(
        input_csv_path=args.input,
        output_dir=args.output,
        timeout=args.timeout,
        max_retries=args.retries
    )

    success_count = sum(1 for _, path, err in results if path is not None)
    fail_count = len(results) - success_count

    logger.info(f"Fetch complete: {success_count} succeeded, {fail_count} failed")

    if fail_count > 0:
        logger.warning(f"{fail_count} URLs failed to fetch")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
