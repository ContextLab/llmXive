"""
HTTP request wrapper with retry logic for data acquisition.
Provides a robust downloader for external datasets (e.g., SPARC) with
exponential backoff and error handling.
"""
import time
import logging
import requests
from typing import Optional, Callable, Any
from pathlib import Path
import hashlib
import re

from utils import setup_logging, ensure_directory

# Configure module logger
logger = setup_logging("download")

DEFAULT_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 1.0
DEFAULT_STATUS_CODES = [429, 500, 502, 503, 504]

# SPARC Official Repository URL Pattern
# The data must originate from the official giacomellil/SPARC repository on GitHub.
# We enforce this to prevent synthetic/fake data injection from unverified sources.
SPARC_REPO_BASE = "https://github.com/giacomellil/SPARC"
VALID_DATA_URLS = [
    "https://github.com/giacomellil/SPARC/raw/master/Data.tar.gz",
    "https://raw.githubusercontent.com/giacomellil/SPARC/master/Data.tar.gz",
]

def fetch_with_retry(
    url: str,
    retries: int = DEFAULT_RETRIES,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    status_forcelist: list = None,
    timeout: int = 30,
    output_path: Optional[Path] = None,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> Optional[Path]:
    """
    Fetch a URL with exponential backoff retry logic.

    Args:
        url: The target URL to download.
        retries: Number of retry attempts.
        backoff_factor: Factor for exponential backoff (seconds).
        status_forcelist: List of HTTP status codes to retry on.
        timeout: Request timeout in seconds.
        output_path: Local path to save the downloaded file. If None, returns the content bytes.
        on_progress: Optional callback(current_bytes, total_bytes) for progress tracking.

    Returns:
        Path to the saved file if output_path is provided, otherwise returns the response content bytes.
        Returns None if all retries fail.

    Raises:
        requests.exceptions.RequestException: If the request fails after retries (logged but not raised here to allow caller handling).
    """
    if status_forcelist is None:
        status_forcelist = DEFAULT_STATUS_CODES

    attempt = 0
    while attempt <= retries:
        try:
            logger.info(f"Fetching {url} (Attempt {attempt + 1}/{retries + 1})")
            response = requests.get(url, timeout=timeout, stream=True)

            # Raise for HTTP errors (4xx, 5xx) that are not in the retry list
            if response.status_code in status_forcelist:
                raise requests.exceptions.HTTPError(f"Status {response.status_code}")

            response.raise_for_status()

            if output_path:
                ensure_directory(output_path)
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if on_progress and total_size > 0:
                                on_progress(downloaded, total_size)
                logger.info(f"Successfully saved {output_path} ({downloaded} bytes)")
                return output_path
            else:
                logger.info("Successfully fetched content (not saving to disk)")
                return response.content

        except requests.exceptions.RequestException as e:
            attempt += 1
            if attempt > retries:
                logger.error(f"Failed to fetch {url} after {retries} retries: {e}")
                return None

            wait_time = backoff_factor * (2 ** (attempt - 1))
            logger.warning(f"Request failed: {e}. Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)

def download_file(
    url: str,
    dest_path: Path,
    retries: int = DEFAULT_RETRIES,
) -> bool:
    """
    Convenience wrapper to download a file to a specific path.

    Args:
        url: Source URL.
        dest_path: Destination file path.
        retries: Number of retries.

    Returns:
        True if successful, False otherwise.
    """
    result = fetch_with_retry(
        url=url,
        retries=retries,
        output_path=Path(dest_path) if dest_path else None
    )
    return result is not None

def validate_url(url: str) -> bool:
    """
    Perform a lightweight check if a URL is reachable without downloading the full content.
    Uses a HEAD request if supported, otherwise GET with stream.

    Returns:
        True if the URL returns a 2xx status code.
    """
    try:
        # Try HEAD first
        resp = requests.head(url, timeout=10, allow_redirects=True)
        if resp.status_code == 200:
            return True
        # Some servers don't support HEAD, fallback to GET (stream only headers)
        if resp.status_code == 405:
            resp = requests.get(url, timeout=10, stream=True)
            resp.close()
            return resp.status_code == 200
        return False
    except requests.exceptions.RequestException:
        return False

def is_valid_sparc_source(url: str) -> bool:
    """
    Validates that the URL originates from the official SPARC repository.
    This ensures no synthetic or fake data sources are used, satisfying FR-001 Data Hygiene.

    Args:
        url: The URL to validate.

    Returns:
        True if the URL matches the official SPARC repository pattern.
    """
    # Normalize URL to handle potential redirects or variations
    url_lower = url.lower()
    
    # Check if it matches the known valid patterns
    for valid_url in VALID_DATA_URLS:
        if url_lower == valid_url.lower():
            return True
    
    # Check against the base repository pattern to catch raw.githubusercontent variations
    if "github.com/giacomellil/sparc" in url_lower or "raw.githubusercontent.com/giacomellil/sparc" in url_lower:
        # Additional check: ensure it points to the Data archive or a known subdirectory
        # This prevents fetching arbitrary files from the repo that might be fake
        if "data.tar.gz" in url_lower or "data/" in url_lower:
            return True
    
    return False

def verify_file_integrity(file_path: Path) -> bool:
    """
    Verifies the integrity of a downloaded SPARC file by checking its SHA-256 hash.
    While the official hash is not hardcoded here to allow for repository updates,
    this function performs a basic sanity check: the file must be non-empty and
    a valid gzip archive (magic bytes).

    Args:
        file_path: Path to the downloaded file.

    Returns:
        True if the file passes basic integrity checks.
    """
    if not file_path.exists():
        logger.error(f"Verification failed: File does not exist at {file_path}")
        return False

    if file_path.stat().st_size == 0:
        logger.error(f"Verification failed: File is empty at {file_path}")
        return False

    try:
        with open(file_path, 'rb') as f:
            # Check for gzip magic bytes (0x1f 0x8b)
            magic = f.read(2)
            if magic != b'\x1f\x8b':
                logger.error(f"Verification failed: File at {file_path} is not a valid gzip archive.")
                return False
        
        logger.info(f"File integrity check passed for {file_path}.")
        return True
    except Exception as e:
        logger.error(f"Verification failed during read: {e}")
        return False

def download_sparc_data(output_dir: Path) -> bool:
    """
    Downloads the SPARC (Spitzer Photometry & Accurate Rotation Curves) dataset.
    This function implements the specific download logic for User Story 1.
    It fetches the main data archive from the official SPARC repository.

    CRITICAL: This function enforces Data Hygiene (FR-001) by:
    1. Validating the source URL against the official SPARC repository.
    2. Verifying the downloaded file's integrity (non-empty, valid gzip).
    3. Refusing to proceed if the source is unverified or the file is corrupted.

    The SPARC data is hosted at:
    https://github.com/giacomellil/SPARC/raw/master/Data.tar.gz

    Args:
        output_dir: Directory where the data archive will be saved.

    Returns:
        True if download was successful and validated, False otherwise.
    """
    # Official SPARC data repository URL
    sparx_url = "https://github.com/giacomellil/SPARC/raw/master/Data.tar.gz"
    
    # 1. Validate Source URL (Data Hygiene)
    if not is_valid_sparc_source(sparx_url):
        logger.error(f"Data Hygiene Violation: URL '{sparx_url}' is not from the official SPARC repository.")
        logger.error("Aborting download to prevent synthetic/fake data usage.")
        return False

    # Ensure output directory exists
    ensure_directory(output_dir)
    
    archive_path = output_dir / "Data.tar.gz"
    
    logger.info(f"Starting SPARC data download to {archive_path}")
    success = download_file(sparx_url, archive_path, retries=5)
    
    if not success:
        logger.error("SPARC data download failed after retries.")
        return False

    # 2. Verify File Integrity (Data Hygiene)
    if not verify_file_integrity(archive_path):
        logger.error("SPARC data integrity check failed. File may be corrupted or synthetic.")
        # Clean up potentially corrupted file
        try:
            archive_path.unlink()
        except OSError:
            pass
        return False
    
    logger.info("SPARC data download and validation completed successfully.")
    return True
