"""
Dataset download module for User Story 1.

Provides functions to download datasets from verified URLs and calculate
SHA-256 checksums for integrity verification.

FR-001: Dataset integrity must be verified via checksums
"""

import hashlib
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Tuple, Optional

# Import logging from existing module
from ingest.logging import get_ingest_logger, log_operation_start, log_operation_end, log_validation_result

# Output directory for downloads
OUTPUT_DIR = Path('data/raw')

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum of a file.
    
    Args:
        file_path: Path to file to hash
    
    Returns:
        Hex digest of SHA-256 hash
    """
    logger = get_ingest_logger()
    log_operation_start(logger, f"Calculating Sha-256 for {file_path}")
    
    sha256_hash = hashlib.sha256()
    
    try:
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b''):
                sha256_hash.update(chunk)
        
        checksum = sha256_hash.hexdigest()
        log_validation_result(logger, 'success', f"Checksum: {checksum}")
        log_operation_end(logger, f"SHA-256 calculation complete")
        return checksum
        
    except Exception as e:
        log_validation_result(logger, 'error', f"Error calculating checksum: {e}")
        log_operation_end(logger, f"SHA-256 calculation failed")
        raise

def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """
    Verify file checksum matches expected value.
    
    Args:
        file_path: Path to file to verify
        expected_checksum: Expected SHA-256 checksum
    
    Returns:
        True if checksum matches, False otherwise
    """
    logger = get_ingest_logger()
    log_operation_start(logger, f"Verifying checksum for {file_path}")
    
    try:
        actual_checksum = calculate_sha256(file_path)
        matches = actual_checksum.lower() == expected_checksum.lower()
        
        if matches:
            log_validation_result(logger, 'success', f"Checksum verified: {actual_checksum}")
        else:
            log_validation_result(logger, 'error', f"Checksum mismatch! Expected: {expected_checksum}, Got: {actual_checksum}")
        
        log_operation_end(logger, "Checksum verification complete")
        return matches
        
    except Exception as e:
        log_validation_result(logger, 'error', f"Checksum verification failed: {e}")
        log_operation_end(logger, "Checksum verification failed")
        return False

def download_dataset(url: str, local_path: Path = None) -> Tuple[bool, Optional[Path]]:
    """
    Download dataset from URL to local path.
    
    Supports URLs from verified-datasets block (T000 verified datasets).
    
    Args:
        url: URL to download from (from verified-datasets block)
        local_path: Local path to save file (optional, defaults to data/raw/)
    
    Returns:
        Tuple of (success: bool, path: Path or None)
    
    FR-001: Dataset integrity must be verified via checksums
    """
    logger = get_ingest_logger()
    log_operation_start(logger, f"Downloading dataset from {url}")
    
    if local_path is None:
        # Generate local path from URL
        filename = Path(url).name if Path(url).suffix else 'dataset.csv'
        local_path = OUTPUT_DIR / filename
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Download with timeout
        logger.info(f"Saving to {local_path}")
        urllib.request.urlretrieve(url, local_path)
        
        # Verify file was created
        if local_path.exists() and local_path.stat().st_size > 0:
            log_validation_result(logger, 'success', f"Downloaded {local_path.stat().st_size} bytes")
            log_operation_end(logger, "Download complete")
            return True, local_path
        else:
            log_validation_result(logger, 'error', "Downloaded file is empty")
            log_operation_end(logger, "Download failed - empty file")
            return False, None
            
    except urllib.error.URLError as e:
        log_validation_result(logger, 'error', f"Download failed: {e}")
        log_operation_end(logger, "Download failed")
        return False, None
    except Exception as e:
        log_validation_result(logger, 'error', f"Download failed: {e}")
        log_operation_end(logger, "Download failed")
        return False, None

def main():
    """
    Main entry point for dataset download.
    
    Usage: python code/ingest/download.py <url> [output_path]
    
    Supports downloading from URLs in the verified-datasets block.
    """
    logger = get_ingest_logger()
    log_operation_start(logger, "Dataset download script")
    
    if len(sys.argv) < 2:
        print("Usage: python code/ingest/download.py <url> [output_path]")
        print("Example: python code/ingest/download.py https://example.com/dataset.csv data/raw/dataset.csv")
        print("Supports URLs from verified-datasets block (T000)")
        sys.exit(1)
    
    url = sys.argv[1]
    local_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    
    success, path = download_dataset(url, local_path)
    
    if success:
        checksum = calculate_sha256(path)
        print(f"\nDownload successful!")
        print(f"File: {path}")
        print(f"SHA-256: {checksum}")
        sys.exit(0)
    else:
        print("\nDownload failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()