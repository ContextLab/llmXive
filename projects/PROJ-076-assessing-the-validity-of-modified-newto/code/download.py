"""
Download module for retrieving and validating external datasets.

This module provides robust HTTP request handling with retry logic,
URL validation, and file integrity verification for the SPARC dataset.
"""

import time
import logging
import requests
from typing import Optional, Callable, Any
from pathlib import Path
import hashlib
import os

# Configure logger
logger = logging.getLogger(__name__)

# Default retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 1.0
DEFAULT_STATUS_FORCE_LIST = [429, 500, 502, 503, 504]
DEFAULT_TIMEOUT = 30  # seconds

def fetch_with_retry(
    url: str,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    status_forcelist: list = None,
    timeout: int = DEFAULT_TIMEOUT,
    headers: Optional[dict] = None
) -> requests.Response:
    """
    Fetch a URL with exponential backoff retry logic.
    
    Args:
        url: The URL to fetch.
        max_retries: Maximum number of retry attempts.
        backoff_factor: Factor for exponential backoff (seconds).
        status_forcelist: List of HTTP status codes to retry on.
        timeout: Request timeout in seconds.
        headers: Optional HTTP headers to include in the request.
    
    Returns:
        The successful requests.Response object.
    
    Raises:
        requests.exceptions.RequestException: If the request fails after all retries.
        ValueError: If the URL is invalid.
    """
    if status_forcelist is None:
        status_forcelist = DEFAULT_STATUS_FORCE_LIST
    
    if not validate_url(url):
        raise ValueError(f"Invalid URL: {url}")
    
    session = requests.Session()
    
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Fetching URL (attempt {attempt + 1}/{max_retries + 1}): {url}")
            response = session.get(url, timeout=timeout, headers=headers)
            
            # Check if response is successful
            if response.ok:
                logger.info(f"Successfully fetched {url}")
                return response
            
            # Check if status code is in force list
            if response.status_code in status_forcelist:
                if attempt < max_retries:
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(
                        f"Received status {response.status_code} for {url}. "
                        f"Retrying in {wait_time:.1f} seconds..."
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Max retries exceeded for {url} with status {response.status_code}")
                    raise requests.exceptions.HTTPError(
                        f"Failed to fetch {url} after {max_retries} retries. "
                        f"Status code: {response.status_code}"
                    )
            else:
                # Non-retryable error
                logger.error(f"Failed to fetch {url}. Status code: {response.status_code}")
                response.raise_for_status()
                
        except requests.exceptions.Timeout:
            if attempt < max_retries:
                wait_time = backoff_factor * (2 ** attempt)
                logger.warning(
                    f"Timeout fetching {url}. Retrying in {wait_time:.1f} seconds..."
                )
                time.sleep(wait_time)
            else:
                logger.error(f"Max retries exceeded for {url} due to timeout.")
                raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            raise
    
    raise requests.exceptions.RequestException(f"Failed to fetch {url} after all retries.")

def download_file(
    url: str,
    destination: Path,
  max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    chunk_size: int = 8192
) -> Path:
    """
    Download a file from a URL to a specified destination with retry logic.
    
    Args:
        url: The URL to download from.
        destination: The local path to save the file.
        max_retries: Maximum number of retry attempts.
        backoff_factor: Factor for exponential backoff.
        chunk_size: Size of chunks to write to disk.
    
    Returns:
        The Path object of the downloaded file.
    
    Raises:
        requests.exceptions.RequestException: If download fails.
        ValueError: If destination is not a valid Path or parent directory doesn't exist.
    """
    if not isinstance(destination, Path):
        destination = Path(destination)
    
    if not destination.parent.exists():
        raise ValueError(f"Parent directory does not exist: {destination.parent}")
    
    # Fetch the content with retry logic
    response = fetch_with_retry(
        url,
        max_retries=max_retries,
        backoff_factor=backoff_factor
    )
    
    # Write to file
    logger.info(f"Writing downloaded content to {destination}")
    with open(destination, 'wb') as f:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:  # Filter out keep-alive chunks
                f.write(chunk)
    
    logger.info(f"Successfully downloaded {url} to {destination}")
    return destination

def validate_url(url: str) -> bool:
    """
    Validate that a string is a well-formed HTTP/HTTPS URL.
    
    Args:
        url: The URL string to validate.
    
    Returns:
        True if valid, False otherwise.
    """
    if not url or not isinstance(url, str):
        return False
    
    if not (url.startswith('http://') or url.startswith('https://')):
        return False
    
    try:
        from urllib.parse import urlparse
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def is_valid_sparc_source(url: str) -> bool:
    """
    Validate that the URL points to a known SPARC dataset source.
    
    Args:
        url: The URL to validate.
    
    Returns:
        True if the URL is a recognized SPARC source, False otherwise.
    """
    # Define known SPARC sources
    spar_sources = [
        'https://github.com/astroandreas/SparcData',
        'https://raw.githubusercontent.com/astroandreas/SparcData',
        'https://github.com/astroandreas/SparcData/raw'
    ]
    
    if not validate_url(url):
        return False
    
    # Check if URL contains any of the known sources
    for source in spar_sources:
        if source in url:
            return True
    
    logger.warning(f"URL {url} is not a recognized SPARC source.")
    return False

def verify_file_integrity(
    file_path: Path,
    expected_md5: Optional[str] = None,
    expected_sha256: Optional[str] = None
) -> bool:
    """
    Verify the integrity of a downloaded file using checksums.
    
    Args:
        file_path: Path to the file to verify.
        expected_md5: Expected MD5 hash (optional).
        expected_sha256: Expected SHA256 hash (optional).
    
    Returns:
        True if verification passes, False otherwise.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If neither hash is provided.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not expected_md5 and not expected_sha256:
        raise ValueError("At least one checksum (MD5 or SHA256) must be provided.")
    
    logger.info(f"Verifying integrity of {file_path}")
    
    md5_hash = hashlib.md5()
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            if expected_md5:
                md5_hash.update(chunk)
            if expected_sha256:
                sha256_hash.update(chunk)
    
    if expected_md5:
        actual_md5 = md5_hash.hexdigest()
        if actual_md5.lower() != expected_md5.lower():
            logger.error(f"MD5 mismatch for {file_path}: expected {expected_md5}, got {actual_md5}")
            return False
        logger.debug(f"MD5 verified for {file_path}: {actual_md5}")
    
    if expected_sha256:
        actual_sha256 = sha256_hash.hexdigest()
        if actual_sha256.lower() != expected_sha256.lower():
            logger.error(f"SHA256 mismatch for {file_path}: expected {expected_sha256}, got {actual_sha256}")
            return False
        logger.debug(f"SHA256 verified for {file_path}: {actual_sha256}")
    
    logger.info(f"File integrity verified: {file_path}")
    return True

def download_sparc_data(
    output_dir: Path,
    source_url: Optional[str] = None,
    verify_checksum: bool = True,
    checksum_file: Optional[Path] = None
) -> Path:
    """
    Download SPARC data with retry logic and integrity verification.
    
    Args:
        output_dir: Directory to save the downloaded data.
        source_url: Optional specific URL to download from.
        verify_checksum: Whether to verify file integrity after download.
        checksum_file: Optional path to a file containing expected checksums.
    
    Returns:
        Path to the downloaded file.
    
    Raises:
        ValueError: If source URL is invalid or missing.
        RuntimeError: If verification fails.
    """
    # Default SPARC data URL (GitHub raw content)
    if not source_url:
        source_url = "https://github.com/astroandreas/SparcData/raw/master/Data.zip"
    
    if not is_valid_sparc_source(source_url):
        logger.warning(f"Source URL {source_url} is not a recognized SPARC source. Proceeding anyway.")
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = "sparc_data.zip"
    destination = output_dir / filename
    
    logger.info(f"Starting download of SPARC data to {destination}")
    download_file(source_url, destination)
    
    if verify_checksum:
        # Attempt to load checksums if provided
        expected_md5 = None
        expected_sha256 = None
        
        if checksum_file and checksum_file.exists():
            logger.info(f"Loading checksums from {checksum_file}")
            with open(checksum_file, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        if parts[1] == 'MD5':
                            expected_md5 = parts[0]
                        elif parts[1] == 'SHA256':
                            expected_sha256 = parts[0]
        
        if not verify_file_integrity(destination, expected_md5, expected_sha256):
            raise RuntimeError(f"Checksum verification failed for {destination}")
    
    logger.info(f"SPARC data successfully downloaded and verified: {destination}")
    return destination
