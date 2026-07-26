"""
Data loading utilities with robust retry logic and checksum verification.

This module provides functions for downloading datasets with exponential backoff,
calculating SHA-256 checksums, and loading specific datasets like QM9, kinetic data,
and reference substructures.
"""
import os
import sys
import time
import logging
import hashlib
import urllib.request
from typing import Optional, Callable, Any

# Add project root to path if needed
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    """
    Calculate the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_with_retry(
    url: str,
    output_path: str,
    max_retries: int = 5,
    base_delay: float = 2.0,
    max_delay: float = 60.0
) -> bool:
    """
    Download a file from a URL with exponential backoff retry logic.
    
    Args:
        url: The URL to download from.
        output_path: The local path to save the file.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay between retries in seconds.
        
    Returns:
        True if download succeeded, False otherwise.
        
    Raises:
        Exception: If download fails after all retries, the last error is logged
                   and the function returns False. The caller must handle the failure.
    """
    last_error = None
    delay = base_delay

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Download attempt {attempt}/{max_retries} for {url}")
            urllib.request.urlretrieve(url, output_path)
            logger.info(f"Successfully downloaded {url} to {output_path}")
            return True
        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt} failed: {e}")
            
            if attempt < max_retries:
                logger.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)
                delay = min(delay * 2, max_delay)  # Exponential backoff with cap
            else:
                logger.error(f"All {max_retries} attempts failed for {url}.")
    
    # If we reach here, all retries failed
    logger.error(f"Failed to download {url} after {max_retries} attempts. Last error: {last_error}")
    return False

def download_qm9_subset(output_path: str) -> bool:
    """
    Download the QM9 subset dataset.
    
    Args:
        output_path: Path to save the downloaded data.
        
    Returns:
        True if successful, False otherwise.
    """
    # Placeholder for QM9 download logic
    # In a real implementation, this would use the datasets library or a verified URL
    logger.warning("QM9 download not fully implemented in this snippet.")
    return False

def download_kinetic_dataset(output_path: str) -> bool:
    """
    Download the kinetic dataset.
    
    Args:
        output_path: Path to save the downloaded data.
        
    Returns:
        True if successful, False otherwise.
    """
    # This function is a placeholder. The actual logic is in 01_download_kinetic_data.py
    # or should be implemented here if needed.
    logger.warning("Kinetic dataset download logic should be in 01_download_kinetic_data.py.")
    return False

def download_reference_substructures(output_path: str) -> bool:
    """
    Download the reference substructures dataset.
    
    Args:
        output_path: Path to save the downloaded data.
        
    Returns:
        True if successful, False otherwise.
    """
    # Placeholder for reference substructures download
    logger.warning("Reference substructures download not fully implemented in this snippet.")
    return False

def main():
    """Main entry point for testing loaders."""
    logger.info("Loaders module loaded successfully.")

if __name__ == "__main__":
    main()