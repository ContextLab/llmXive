"""
Data download module for the Moral Machine dataset.

Fetches a subset of the Moral Machine data (<= 50k rows) with fallback logic
for broken URLs. Implements FR-001.
"""
import os
import sys
import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import requests
import pandas as pd
from urllib.parse import urljoin

# Project-relative imports
from utils.logger import get_logger, log_error_to_file
from utils.checksum import compute_file_sha256

# Configure logging for this module
logger = get_logger(__name__)

# Constants
MORAL_MACHINE_BASE_URL = "https://storage.googleapis.com/moral-machine/moral_machine_data.csv"
FALLBACK_URLS = [
    "https://raw.githubusercontent.com/ProjectMoralMachine/dataset/main/moral_machine_data.csv",
    "https://storage.googleapis.com/moral-machine/moral_machine_data_backup.csv",
]
MAX_ROWS = 50000
CHECKSUM_FILE = "data/raw/moral_machine_checksum.txt"
RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"

def download_from_url(
    url: str, 
    output_path: Path, 
    max_rows: int = MAX_ROWS,
    timeout: int = 30
) -> Tuple[bool, Optional[str]]:
    """
    Download data from a URL and save to output_path.
    
    Args:
        url: The URL to download from
        output_path: Path to save the downloaded file
        max_rows: Maximum number of rows to fetch (if supported by source)
        timeout: Request timeout in seconds
        
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    logger.info(f"Attempting to download from: {url}")
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # For CSV sources that support streaming, we'll read line by line
        # to respect max_rows limit
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Validate file size
        file_size = output_path.stat().st_size
        if file_size == 0:
            return False, "Downloaded file is empty"
        
        logger.info(f"Successfully downloaded {file_size} bytes from {url}")
        return True, None
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to download from {url}: {str(e)}"
        logger.warning(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error downloading from {url}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def verify_checksum(file_path: Path) -> bool:
    """
    Verify the checksum of a downloaded file.
    
    Args:
        file_path: Path to the file to verify
        
    Returns:
        True if checksum matches or no checksum file exists, False otherwise
    """
    if not file_path.exists():
        return False
        
    current_checksum = compute_file_sha256(file_path)
    checksum_file = Path(RAW_DATA_DIR) / CHECKSUM_FILE
    
    if checksum_file.exists():
        with open(checksum_file, 'r') as f:
            stored_checksum = f.read().strip()
            if current_checksum != stored_checksum:
                logger.warning(f"Checksum mismatch for {file_path}")
                logger.warning(f"  Stored: {stored_checksum}")
                logger.warning(f"  Current: {current_checksum}")
                return False
        logger.info(f"Checksum verified for {file_path}")
        return True
    else:
        # Save new checksum
        checksum_file.parent.mkdir(parents=True, exist_ok=True)
        with open(checksum_file, 'w') as f:
            f.write(current_checksum)
        logger.info(f"Saved checksum for {file_path}")
        return True

def subset_csv(input_path: Path, output_path: Path, max_rows: int = MAX_ROWS) -> bool:
    """
    Create a subset of the CSV file with specified maximum rows.
    
    Args:
        input_path: Path to the full CSV file
        output_path: Path to save the subset
        max_rows: Maximum number of rows to include
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Creating subset of {input_path} with max {max_rows} rows")
        
        # Read only the header and first max_rows+1 lines (header + data)
        df = pd.read_csv(input_path, nrows=max_rows)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        
        logger.info(f"Created subset with {len(df)} rows at {output_path}")
        return True
        
    except Exception as e:
        error_msg = f"Failed to create subset: {str(e)}"
        logger.error(error_msg)
        return False

def download_moral_machine_data(
    target_dir: Optional[Path] = None,
    max_rows: int = MAX_ROWS
) -> Tuple[bool, Path, Optional[str]]:
    """
    Main function to download and prepare Moral Machine data.
    
    Implements FR-001: Fetches data with broken-URL fallback logic.
    
    Args:
        target_dir: Directory to save the data (defaults to data/raw)
        max_rows: Maximum number of rows to fetch
        
    Returns:
        Tuple of (success: bool, output_path: Path, error_message: Optional[str])
    """
    if target_dir is None:
        target_dir = Path(RAW_DATA_DIR)
        
    target_dir.mkdir(parents=True, exist_ok=True)
    full_output = target_dir / "moral_machine_full.csv"
    subset_output = target_dir / "moral_machine_subset.csv"
    
    # Try primary URL
    all_urls = [MORAL_MACHINE_BASE_URL] + FALLBACK_URLS
    
    for url in all_urls:
        logger.info(f"Trying URL: {url}")
        success, error = download_from_url(url, full_output, max_rows=None)
        
        if success:
            # Verify checksum
            if verify_checksum(full_output):
                # Create subset
                if subset_csv(full_output, subset_output, max_rows):
                    # Remove full file to save space
                    try:
                        full_output.unlink()
                        logger.info(f"Removed full file: {full_output}")
                    except Exception as e:
                        logger.warning(f"Could not remove full file: {e}")
                    
                    return True, subset_output, None
                else:
                    return False, subset_output, "Failed to create subset"
            else:
                return False, full_output, "Checksum verification failed"
        else:
            logger.warning(f"Failed to download from {url}: {error}")
            continue
    
    # All URLs failed
    error_msg = f"All download URLs failed. Last error: {error}"
    log_error_to_file(error_msg, "data_download_errors.log")
    return False, subset_output, error_msg

def main():
    """Main entry point for downloading data."""
    logger.info("Starting Moral Machine data download")
    
    success, output_path, error = download_moral_machine_data()
    
    if success:
        logger.info(f"Download completed successfully: {output_path}")
        print(f"SUCCESS: Data downloaded to {output_path}")
        sys.exit(0)
    else:
        logger.error(f"Download failed: {error}")
        print(f"FAILED: {error}")
        sys.exit(1)

if __name__ == "__main__":
    main()
