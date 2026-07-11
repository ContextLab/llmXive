"""
Data loader for MulTaBench ingestion with local checksum verification.
Supports local file verification and URL-based dataset fetching with integrity checks.
"""
import os
import hashlib
import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import time

from utils.logging import get_logger, log_info, log_error, log_warning

logger = get_logger(__name__)

# Configuration for download retries
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    Reads the file in chunks to handle large files efficiently.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        log_error(logger, f"Failed to compute checksum for {file_path}: {e}")
        raise

def load_checksums(checksum_file: Path) -> Dict[str, str]:
    """
    Load expected checksums from a JSON file.
    Expected format: {"filename_or_url_key": "sha256_hash", ...}
    """
    if not checksum_file.exists():
        log_error(logger, f"Checksum file not found: {checksum_file}")
        raise FileNotFoundError(f"Checksum file not found: {checksum_file}")
    
    try:
        with open(checksum_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        log_error(logger, f"Invalid JSON in checksum file {checksum_file}: {e}")
        raise

def verify_checksum(file_path: Path, expected_hash: str) -> bool:
    """
    Verify the SHA-256 checksum of a file against an expected value.
    """
    if not file_path.exists():
        log_error(logger, f"File does not exist for verification: {file_path}")
        return False

    actual_hash = compute_sha256(file_path)
    if actual_hash != expected_hash:
        log_error(logger, f"Checksum mismatch for {file_path}. Expected: {expected_hash}, Got: {actual_hash}")
        return False
    
    log_info(logger, f"Checksum verified successfully for {file_path}")
    return True

def download_file_with_retry(url: str, dest_path: Path) -> Tuple[bool, str]:
    """
    Download a file from a URL with retry logic.
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log_info(logger, f"Downloading {url} to {dest_path} (Attempt {attempt}/{MAX_RETRIES})")
            urllib.request.urlretrieve(url, dest_path)
            
            # Verify size is non-zero
            if dest_path.stat().st_size == 0:
                raise ValueError("Downloaded file is empty.")
            
            log_info(logger, f"Download completed successfully: {dest_path}")
            return True, "Download successful"
            
        except urllib.error.URLError as e:
            log_warning(logger, f"Network error during download (Attempt {attempt}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                return False, f"Network error after {MAX_RETRIES} attempts: {e}"
        except Exception as e:
            log_error(logger, f"Unexpected error during download: {e}")
            return False, f"Download failed: {e}"
    
    return False, "Max retries exceeded"

def ingest_dataset(
    dataset_name: str,
    data_dir: Path,
    checksum_file: Optional[Path] = None,
    url_mapping: Optional[Dict[str, str]] = None
) -> Tuple[bool, str]:
    """
    Ingest a dataset, verifying its checksum if a checksum file is provided.
    If the dataset is not found locally, attempts to download it if a URL mapping is provided.
    
    Args:
        dataset_name: Name of the dataset (folder, file, or key in url_mapping).
        data_dir: Directory containing the raw data or where it should be downloaded.
        checksum_file: Optional path to a JSON file containing expected checksums.
        url_mapping: Optional dict mapping dataset names to download URLs.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = data_dir / dataset_name
    
    # Check if file exists locally
    if dataset_path.exists():
        log_info(logger, f"Dataset found locally: {dataset_path}")
    else:
        # Attempt download if URL mapping provided
        if url_mapping and dataset_name in url_mapping:
            url = url_mapping[dataset_name]
            success, msg = download_file_with_retry(url, dataset_path)
            if not success:
                return False, f"Download failed: {msg}"
            log_info(logger, f"Dataset downloaded: {dataset_path}")
        else:
            log_error(logger, f"Dataset not found locally and no URL provided: {dataset_path}")
            return False, f"Dataset not found: {dataset_name}"

    # Checksum verification
    if checksum_file:
        try:
            checksums = load_checksums(checksum_file)
            # Support both filename key and dataset_name key
            expected_hash = checksums.get(dataset_name) or checksums.get(dataset_path.name)
            
            if expected_hash is None:
                log_warning(logger, f"No checksum entry for {dataset_name}, skipping verification.")
            else:
                if verify_checksum(dataset_path, expected_hash):
                    return True, f"Dataset {dataset_name} verified and ingested."
                else:
                    return False, f"Checksum verification failed for {dataset_name}."
        except Exception as e:
            log_error(logger, f"Error during checksum verification: {e}")
            return False, f"Checksum verification error: {e}"
    
    log_info(logger, f"Dataset {dataset_name} ingested without checksum verification.")
    return True, f"Dataset {dataset_name} ingested."

def main():
    """
    Main entry point for data loading script.
    Demonstrates usage with local paths and optional checksum verification.
    """
    # Configuration
    data_dir = Path("data/raw")
    checksum_file = data_dir / "checksums.json"
    
    # Example dataset key (must exist in checksums.json or url_mapping)
    dataset_name = "multabench_sample"
    
    # Example URL mapping (replace with real MulTaBench URLs if available)
    # This is a placeholder; real implementation would map to actual data sources
    url_mapping = {
        "multabench_sample": "https://example.com/multabench_sample.zip" 
    }
    
    log_info(logger, f"Starting data ingestion for {dataset_name}")
    success, message = ingest_dataset(dataset_name, data_dir, checksum_file, url_mapping)
    
    if success:
        print(f"Success: {message}")
    else:
        print(f"Failed: {message}")
        # Exit with error code to signal failure in CI/CD pipelines
        exit(1)

if __name__ == "__main__":
    main()