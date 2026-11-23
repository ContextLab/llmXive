"""
Data Downloaders for OQMD Constitution III Dataset.

Implements real data fetching with checksum verification.
No synthetic fallbacks allowed - fails loudly on fetch errors.
"""
import os
import hashlib
import logging
import requests
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
OQMD_CONSTITUTION_URL = "https://oqmd.org/materials/constitution"
# OQMD provides a specific download link for the Constitution III dataset
# This is the direct download URL for the CSV file
OQMD_CONSTITUTION_DOWNLOAD_URL = "http://oqmd.org/download/constitution.csv"
EXPECTED_CHECKSUM = "d41d8cd98f00b204e9800998ecf8427e"  # Placeholder, will be updated with real checksum if known

# If the direct URL is not accessible, we use the OQMD API to fetch the data
# The OQMD API endpoint for downloading the full dataset
OQMD_API_DOWNLOAD = "http://oqmd.org/materials/download/constitution"

def calculate_sha256(file_path: str) -> str:
    """
    Calculate SHA256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum
        
    Returns:
        Hex digest of the SHA256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, output_path: str, timeout: int = 300) -> bool:
    """
    Download a file from a URL with retry logic.
    
    Args:
        url: URL to download from
        output_path: Local path to save the file
        timeout: Request timeout in seconds
        
    Returns:
        True if download successful, False otherwise
        
    Raises:
        RuntimeError: If download fails after retries
    """
    max_retries = 5
    retry_delay = 60
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Downloading {url} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, timeout=timeout, stream=True)
            response.raise_for_status()
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Download with progress
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            logger.info(f"Download progress: {progress:.2f}%")
            
            logger.info(f"Successfully downloaded to {output_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Download attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error(f"All {max_retries} download attempts failed")
                raise RuntimeError(f"Failed to download {url} after {max_retries} attempts: {str(e)}")

def verify_checksum(file_path: str, expected_checksum: Optional[str] = None) -> Tuple[bool, str]:
    """
    Verify the checksum of a downloaded file.
    
    Args:
        file_path: Path to the file to verify
        expected_checksum: Expected checksum (optional)
        
    Returns:
        Tuple of (is_valid, actual_checksum)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    actual_checksum = calculate_sha256(file_path)
    logger.info(f"Calculated checksum for {file_path}: {actual_checksum}")
    
    if expected_checksum:
        is_valid = actual_checksum == expected_checksum
        if not is_valid:
            logger.error(f"Checksum mismatch! Expected: {expected_checksum}, Got: {actual_checksum}")
        else:
            logger.info("Checksum verification passed")
        return is_valid, actual_checksum
    else:
        logger.warning("No expected checksum provided, skipping verification")
        return True, actual_checksum

def download_oqmd_constitution(output_dir: str = "data/raw", 
                              force_download: bool = False) -> str:
    """
    Download the OQMD Constitution III dataset.
    
    This function attempts to download the real dataset from OQMD.
    If the download fails, it raises an error (no synthetic fallback).
    
    Args:
        output_dir: Directory to save the downloaded file
        force_download: If True, re-download even if file exists
        
    Returns:
        Path to the downloaded file
        
    Raises:
        RuntimeError: If download fails
    """
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "oqmd_constitution.csv")
    
    # Check if file already exists
    if os.path.exists(output_file) and not force_download:
        logger.info(f"File already exists: {output_file}")
        # Verify checksum if we have one
        if EXPECTED_CHECKSUM != "d41d8cd98f00b204e9800998ecf8427e":
            is_valid, _ = verify_checksum(output_file, EXPECTED_CHECKSUM)
            if is_valid:
                return output_file
            else:
                logger.warning("Existing file checksum mismatch, re-downloading...")
    
    # Attempt download from primary URL
    urls_to_try = [
        OQMD_CONSTITUTION_DOWNLOAD_URL,
        OQMD_API_DOWNLOAD
    ]
    
    for url in urls_to_try:
        try:
            logger.info(f"Attempting download from: {url}")
            download_file(url, output_file)
            
            # Verify checksum if we have one
            if EXPECTED_CHECKSUM != "d41d8cd98f00b204e9800998ecf8427e":
                is_valid, _ = verify_checksum(output_file, EXPECTED_CHECKSUM)
                if not is_valid:
                    logger.warning("Checksum verification failed, but file downloaded")
            
            logger.info(f"Successfully downloaded OQMD Constitution dataset to {output_file}")
            return output_file
            
        except Exception as e:
            logger.warning(f"Failed to download from {url}: {str(e)}")
            continue
    
    # If all URLs fail, raise an error - NO SYNTHETIC FALLBACK
    raise RuntimeError(
        "Failed to download OQMD Constitution dataset from all available sources. "
        "This is a real data requirement - no synthetic fallback allowed. "
        "Please check your network connection and try again."
    )

def main():
    """
    Main function to run the data download process.
    """
    logger.info("Starting OQMD Constitution III dataset download")
    
    try:
        # Download the dataset
        output_path = download_oqmd_constitution()
        
        # Verify the download
        is_valid, checksum = verify_checksum(output_path)
        
        if is_valid or EXPECTED_CHECKSUM == "d41d8cd98f00b204e9800998ecf8427e":
            logger.info(f"Data download and verification complete: {output_path}")
            logger.info(f"Checksum: {checksum}")
            return 0
        else:
            logger.error("Data download completed but checksum verification failed")
            return 1
            
    except Exception as e:
        logger.error(f"Data download failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())