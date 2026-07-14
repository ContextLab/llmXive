"""
Robust dataset loaders with exponential backoff retry logic.

This module provides utilities for downloading datasets from external sources
with retry mechanisms, error logging, and clear exit codes for orchestration.
"""
import os
import sys
import time
import logging
import hashlib
import urllib.request
import urllib.error
from typing import Optional, Tuple
from pathlib import Path

# Configure logging for this module
logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 5
BASE_DELAY = 2.0  # seconds
MAX_DELAY = 60.0  # seconds

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_with_retry(
    url: str,
    output_path: str,
    expected_checksum: Optional[str] = None,
    max_retries: int = MAX_RETRIES,
    base_delay: float = BASE_DELAY,
    max_delay: float = MAX_DELAY
) -> Tuple[bool, str]:
    """
    Download a file from a URL with exponential backoff retry logic.
    
    Args:
        url: The URL to download from
        output_path: Local path to save the downloaded file
        expected_checksum: Optional SHA-256 checksum to verify against
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    attempt = 0
    last_error = None
    
    while attempt < max_retries:
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries}: Downloading {url}")
            
            # Perform download
            urllib.request.urlretrieve(url, output_path)
            
            # Verify checksum if provided
            if expected_checksum:
                actual_checksum = calculate_sha256(output_path)
                if actual_checksum.lower() != expected_checksum.lower():
                    error_msg = (
                        f"Checksum mismatch for {output_path}. "
                        f"Expected: {expected_checksum}, Got: {actual_checksum}"
                    )
                    logger.error(error_msg)
                    # Clean up failed file
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    return False, error_msg
                logger.info(f"Checksum verified: {actual_checksum}")
            
            logger.info(f"Successfully downloaded {url} to {output_path}")
            return True, "Download successful"
            
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            last_error = str(e)
            attempt += 1
            
            if attempt >= max_retries:
                error_msg = (
                    f"Download failed after {max_retries} attempts. "
                    f"Last error: {last_error}. URL: {url}"
                )
                logger.error(error_msg)
                return False, error_msg
            
            # Exponential backoff with jitter
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            logger.warning(
                f"Download attempt {attempt} failed: {last_error}. "
                f"Retrying in {delay:.1f} seconds..."
            )
            time.sleep(delay)
    
    # Should not reach here, but handle gracefully
    error_msg = f"Unexpected termination of download loop for {url}"
    logger.error(error_msg)
    return False, error_msg

def download_qm9_subset(
    output_path: str,
    expected_checksum: Optional[str] = None,
    max_retries: int = MAX_RETRIES
) -> Tuple[bool, str]:
    """
    Download QM9 subset from a verified source.
    
    Args:
        output_path: Local path to save the dataset
        expected_checksum: Optional SHA-256 checksum for verification
        max_retries: Maximum retry attempts
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Using a verified source: QM9 from MoleculeNet or similar
    # This is a representative URL - in production, use the actual verified source
    url = "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/molnet_publish/qm9.zip"
    
    success, message = download_with_retry(
        url=url,
        output_path=output_path,
        expected_checksum=expected_checksum,
        max_retries=max_retries
    )
    
    return success, message

def download_kinetic_dataset(
    output_path: str,
    expected_checksum: Optional[str] = None,
    max_retries: int = MAX_RETRIES
) -> Tuple[bool, str]:
    """
    Download external kinetic dataset from a verified source.
    
    Args:
        output_path: Local path to save the dataset
        expected_checksum: Optional SHA-256 checksum for verification
        max_retries: Maximum retry attempts
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Placeholder for actual verified source URL
    # In production, replace with the real source URL from spec
    url = "https://example.com/kinetic_dataset.csv"
    
    success, message = download_with_retry(
        url=url,
        output_path=output_path,
        expected_checksum=expected_checksum,
        max_retries=max_retries
    )
    
    return success, message

def download_reference_substructures(
    output_path: str,
    expected_checksum: Optional[str] = None,
    max_retries: int = MAX_RETRIES
) -> Tuple[bool, str]:
    """
    Download curated reference set of known reactive substructures.
    
    Args:
        output_path: Local path to save the dataset
        expected_checksum: Optional SHA-256 checksum for verification
        max_retries: Maximum retry attempts
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Placeholder for actual verified source URL
    url = "https://example.com/reference_substructures.csv"
    
    success, message = download_with_retry(
        url=url,
        output_path=output_path,
        expected_checksum=expected_checksum,
        max_retries=max_retries
    )
    
    return success, message

def main():
    """
    Main entry point for standalone execution.
    
    Demonstrates the retry logic and error handling.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('artifacts/logs/loader_test.log')
        ]
    )
    
    # Test with a real URL
    test_url = "https://raw.githubusercontent.com/deepchem/deepchem/master/data/qm9.csv"
    output_file = "data/raw/qm9_test.csv"
    
    logger.info("Starting download test...")
    success, message = download_with_retry(test_url, output_file)
    
    if success:
        logger.info(f"SUCCESS: {message}")
        sys.exit(0)
    else:
        logger.error(f"FAILED: {message}")
        sys.exit(1)

if __name__ == "__main__":
    main()
