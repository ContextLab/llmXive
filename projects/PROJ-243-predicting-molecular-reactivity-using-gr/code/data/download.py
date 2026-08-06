import os
import sys
import time
import logging
import hashlib
import urllib.request
import urllib.error
from typing import Optional, Tuple
from config import get_config

def setup_script_logging() -> logging.Logger:
    """Configure logging for download scripts."""
    logger = logging.getLogger("download")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def download_with_retry(
    url: str,
    output_path: str,
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    logger: Optional[logging.Logger] = None,
) -> Tuple[bool, str]:
    """
    Download a file from a URL with exponential backoff retry logic.

    Args:
        url: The URL to download from.
        output_path: The local path to save the file to.
        max_retries: Maximum number of retry attempts.
        backoff_factor: Factor for exponential backoff in seconds.
        logger: Optional logger instance.

    Returns:
        Tuple of (success: bool, message: str)
    """
    if logger is None:
        logger = setup_script_logging()

    attempt = 0
    while attempt < max_retries:
        try:
            logger.info(f"Attempting download (attempt {attempt + 1}/{max_retries}) from {url}")
            urllib.request.urlretrieve(url, output_path)
            logger.info(f"Successfully downloaded to {output_path}")
            return True, "Download successful"
        except urllib.error.URLError as e:
            attempt += 1
            if attempt == max_retries:
                logger.error(f"Failed to download after {max_retries} attempts: {e}")
                return False, f"URLError: {e}"
            wait_time = backoff_factor ** attempt
            logger.warning(f"Download failed: {e}. Retrying in {wait_time}s...")
            time.sleep(wait_time)
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            return False, f"Unexpected error: {e}"

    return False, "Max retries exceeded"

def calculate_sha256(file_path: str) -> str:
    """Calculate the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def orchestrate_download(
    dataset_name: str,
    url: str,
    output_filename: str,
    expected_hash: Optional[str] = None,
    logger: Optional[logging.Logger] = None,
) -> bool:
    """
    Orchestrate the download of a dataset, verifying the checksum if provided.

    Args:
        dataset_name: Name of the dataset for logging.
        url: URL to download from.
        output_filename: Filename to save as (relative to data/raw).
        expected_hash: Expected SHA-256 hash for verification.
        logger: Optional logger.

    Returns:
        True if download and verification succeed, False otherwise.
    """
    if logger is None:
        logger = setup_script_logging()

    config = get_config()
    raw_dir = os.path.join(config["data_dir"], "raw")
    os.makedirs(raw_dir, exist_ok=True)

    output_path = os.path.join(raw_dir, output_filename)

    # Download
    success, msg = download_with_retry(url, output_path, logger=logger)
    if not success:
        logger.error(f"Download failed for {dataset_name}: {msg}")
        return False

    # Verify checksum if expected hash is provided
    if expected_hash:
        logger.info(f"Verifying checksum for {output_filename}...")
        actual_hash = calculate_sha256(output_path)
        if actual_hash != expected_hash:
            logger.error(
                f"Checksum mismatch for {dataset_name}. "
                f"Expected: {expected_hash}, Got: {actual_hash}"
            )
            return False
        logger.info("Checksum verification passed.")

    return True

def main():
    """Entry point for manual execution."""
    logger = setup_script_logging()
    logger.info("Starting download orchestration.")
    # Example usage would be passed via CLI args or config
    # For now, just log that it's ready
    logger.info("Ready to orchestrate downloads.")

if __name__ == "__main__":
    main()
