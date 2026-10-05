import os
import time
import hashlib
import json
import requests
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path
import logging
import sys

# Configure logging for this module
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Configuration constants
MAX_RETRIES = 5
INITIAL_DELAY = 1.0
MAX_DELAY = 60.0
BACKOFF_MULTIPLIER = 2.0
CHUNK_SIZE = 8192

def calculate_md5(file_path: str) -> str:
    """
    Calculate the MD5 checksum of a file.

    Args:
        file_path: Path to the file to calculate checksum for.

    Returns:
        Hexadecimal string of the MD5 checksum.
    """
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum calculation: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error calculating MD5 for {file_path}: {e}")
        raise

def exponential_backoff_retry(func, max_retries: int = MAX_RETRIES,
                              initial_delay: float = INITIAL_DELAY,
                              max_delay: float = MAX_DELAY,
                              backoff_multiplier: float = BACKOFF_MULTIPLIER):
    """
    Decorator to retry a function with exponential backoff.

    Args:
        func: The function to retry.
        max_retries: Maximum number of retry attempts.
        initial_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
        backoff_multiplier: Multiplier for the delay.

    Returns:
        The result of the function if successful, otherwise raises the last exception.
    """
    def wrapper(*args, **kwargs):
        delay = initial_delay
        last_exception = None

        for attempt in range(1, max_retries + 1):
            try:
                return func(*args, **kwargs)
            except (requests.exceptions.RequestException, OSError) as e:
                last_exception = e
                if attempt == max_retries:
                    logger.error(f"Attempt {attempt} failed. No more retries left. Error: {e}")
                    raise
                else:
                    logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay:.2f}s...")
                    time.sleep(delay)
                    delay = min(delay * backoff_multiplier, max_delay)

        raise last_exception  # Should not reach here due to return/raise above
    return wrapper

def verify_try_url_access(url: str, timeout: int = 10) -> Tuple[bool, str]:
    """
    Verify if the TRY database URL is accessible and returns a valid CSV.

    Args:
        url: The URL to check.
        timeout: Request timeout in seconds.

    Returns:
        Tuple of (is_accessible, message).
    """
    try:
        logger.info(f"Verifying URL access: {url}")
        # Use HEAD request first if possible, fallback to GET with small limit
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        if response.status_code == 405: # Method Not Allowed
            response = requests.get(url, timeout=timeout, stream=True, allow_redirects=True)
            # Just read a small chunk to verify it's a CSV stream
            next(response.iter_content(chunk_size=1024))
        else:
            response.raise_for_status()

        content_type = response.headers.get('Content-Type', '')
        if 'text/csv' in content_type or response.url.endswith('.csv'):
            return True, f"URL accessible and appears to be CSV (Status: {response.status_code})"
        else:
            return False, f"URL accessible but content type '{content_type}' is unexpected."

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return False, "HTTP 404: Resource not found."
        elif e.response.status_code == 403:
            return False, "HTTP 403: Forbidden. Access denied."
        else:
            return False, f"HTTP Error: {e.response.status_code} - {e}"
    except requests.exceptions.RequestException as e:
        return False, f"Request failed: {e}"
    except Exception as e:
        return False, f"Unexpected error during verification: {e}"

@exponential_backoff_retry
def _download_file(url: str, destination: str) -> None:
    """
    Internal function to download a file with streaming.

    Args:
        url: Source URL.
        destination: Local destination path.
    """
    response = requests.get(url, stream=True, timeout=300)
    response.raise_for_status()
    with open(destination, 'wb') as f:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                f.write(chunk)

def download_try_data(try_url: str, output_dir: str, expected_md5: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch TRY database CSVs with exponential backoff and checksum verification.

    Args:
        try_url: URL to the TRY database CSV.
        output_dir: Directory to save the downloaded file.
        expected_md5: Optional expected MD5 checksum for verification.

    Returns:
        Dictionary with 'status' (SUCCESS/FAILED), 'message', 'file_path', 'md5'.
    """
    os.makedirs(output_dir, exist_ok=True)
    filename = os.path.basename(try_url.split('?')[0]) # Handle query params
    if not filename.endswith('.csv'):
        filename = "try_data.csv"
    local_path = os.path.join(output_dir, filename)

    logger.info(f"Starting download from {try_url}")
    logger.info(f"Destination: {local_path}")

    # 1. Verify URL access
    is_accessible, access_msg = verify_try_url_access(try_url)
    if not is_accessible:
        logger.error(f"URL verification failed: {access_msg}")
        return {
            "status": "FAILED",
            "message": access_msg,
            "file_path": None,
            "md5": None
        }

    # 2. Download with retry logic
    try:
        _download_file(try_url, local_path)
        logger.info(f"Download completed successfully to {local_path}")
    except Exception as e:
        logger.error(f"Download failed after retries: {e}")
        return {
            "status": "FAILED",
            "message": f"Download failed: {e}",
            "file_path": None,
            "md5": None
        }

    # 3. Verify Checksum
    actual_md5 = calculate_md5(local_path)
    logger.info(f"Calculated MD5: {actual_md5}")

    if expected_md5:
        if actual_md5.lower() != expected_md5.lower():
            error_msg = f"Checksum mismatch! Expected: {expected_md5}, Got: {actual_md5}"
            logger.error(error_msg)
            # Remove corrupted file
            try:
                os.remove(local_path)
            except OSError:
                pass
            return {
                "status": "FAILED",
                "message": error_msg,
                "file_path": None,
                "md5": actual_md5
            }
        else:
            logger.info("Checksum verification passed.")
    else:
        logger.warning("No expected MD5 provided, skipping checksum verification.")

    return {
        "status": "SUCCESS",
        "message": "Download and verification successful.",
        "file_path": local_path,
        "md5": actual_md5
    }

def fetch_ncbi_refseq(species_list: List[str], output_dir: str) -> Dict[str, Any]:
    """
    Fetch NCBI RefSeq genomic annotation files for the species list.
    Note: This is a placeholder for the actual implementation of T011b.
    The logic for real fetch vs synthetic fallback is handled in T011b.
    """
    logger.info(f"Fetching NCBI RefSeq for {len(species_list)} species")
    # Implementation details for T011b
    return {"status": "PENDING", "message": "Logic implemented in T011b"}

def fetch_tree(species_list: List[str], output_dir: str) -> Dict[str, Any]:
    """
    Fetch a real phylogenetic tree from OpenTree of Life.
    Note: This is a placeholder for the actual implementation of T016c.
    """
    logger.info(f"Fetching phylogenetic tree for {len(species_list)} species")
    # Implementation details for T016c
    return {"status": "PENDING", "message": "Logic implemented in T016c"}

def main():
    """
    Main entry point for downloading TRY data.
    Reads configuration from config.py if available, otherwise uses defaults.
    """
    from config import get_config, ensure_directories

    config = get_config()
    ensure_directories([config.get('output_dir', 'data/raw')])

    try_url = config.get('try_url')
    if not try_url:
        logger.error("TRY URL not found in configuration. Exiting.")
        return {"status": "FAILED", "message": "Missing TRY URL in config"}

    result = download_try_data(
        try_url=try_url,
        output_dir=config.get('output_dir', 'data/raw'),
        expected_md5=config.get('expected_try_md5')
    )

    logger.info(f"Final Status: {result['status']}")
    if result['status'] == 'SUCCESS':
        logger.info(f"File saved at: {result['file_path']}")
        logger.info(f"MD5: {result['md5']}")
    else:
        logger.error(f"Error: {result['message']}")

    return result

if __name__ == "__main__":
    main()