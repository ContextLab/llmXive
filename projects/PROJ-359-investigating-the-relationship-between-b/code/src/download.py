"""
Data download module for fetching ds000278 (OpenNeuro HCP rs-fMRI release).

This module handles:
- Fetching dataset metadata from OpenNeuro API
- Downloading specific resting-state files
- Verifying checksums
- Handling HTTP errors and dataset availability checks

Mandatory: Must download ds000278 which contains required resting-state scans.
"""

import os
import sys
import hashlib
import json
import time
import requests
from pathlib import Path
from urllib.parse import urljoin

# Constants
OPENNEURO_API_BASE = "https://api.openneuro.org"
DATASET_ID = "ds000278"
REQUIRED_FILE_PATTERN = "*_space-MNI_desc-preproc_bold.nii.gz"
OUTPUT_DIR = "data/raw"
CHECKSUM_FILE = "data/raw/checksums.json"
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Import from utils for logging and seeding
try:
    from src.utils import log_event, setup_logging, get_log_path
except ImportError:
    # Fallback for standalone execution during testing
    def log_event(msg, level="INFO"):
        print(f"[{level}] {msg}")
    
    def setup_logging():
        pass

def get_dataset_metadata(dataset_id):
    """
    Fetch dataset metadata from OpenNeuro API.
    
    Args:
        dataset_id: The OpenNeuro dataset identifier (e.g., 'ds000278')
        
    Returns:
        dict: Dataset metadata including version, description, etc.
        
    Raises:
        requests.HTTPError: If dataset is not found or API fails
    """
    url = f"{OPENNEURO_API_BASE}/datasets/{dataset_id}"
    headers = {
        "Accept": "application/json",
        "User-Agent": "llmXive-pipeline/1.0"
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                raise
            log_event(f"Retry {attempt + 1}/{MAX_RETRIES} for metadata fetch: {e}", "WARNING")
            time.sleep(RETRY_DELAY)

def get_dataset_files(dataset_id, version=None):
    """
    Fetch list of files in the dataset.
    
    Args:
        dataset_id: The OpenNeuro dataset identifier
        version: Optional specific version (defaults to latest)
        
    Returns:
        list: List of file objects with path, size, and checksum info
        
    Raises:
        requests.HTTPError: If file list cannot be retrieved
    """
    url = f"{OPENNEURO_API_BASE}/datasets/{dataset_id}/files"
    params = {}
    if version:
        params["version"] = version
        
    headers = {
        "Accept": "application/json",
        "User-Agent": "llmXive-pipeline/1.0"
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                raise
            log_event(f"Retry {attempt + 1}/{MAX_RETRIES} for file list: {e}", "WARNING")
            time.sleep(RETRY_DELAY)

def find_resting_state_files(file_list, dataset_id):
    """
    Find resting-state BOLD files matching the required pattern.
    
    Args:
        file_list: List of file objects from get_dataset_files
        dataset_id: Dataset identifier for error messages
        
    Returns:
        list: List of file objects that match the resting-state pattern
        
    Raises:
        FileNotFoundError: If no matching resting-state files are found
    """
    matching_files = []
    
    for file_obj in file_list:
        file_path = file_obj.get("filename", "")
        
        # Check for resting-state BOLD files with MNI space and preproc description
        if (file_path.startswith("sub-") and 
            "/func/" in file_path and 
            "space-MNI" in file_path and 
            "desc-preproc" in file_path and 
            file_path.endswith("_bold.nii.gz")):
            matching_files.append(file_obj)
    
    if not matching_files:
        error_msg = f"Required resting-state dataset {dataset_id} not found. " \
                   f"No files matching pattern '*_space-MNI_desc-preproc_bold.nii.gz' found."
        log_event(error_msg, "ERROR")
        raise FileNotFoundError(error_msg)
    
    log_event(f"Found {len(matching_files)} resting-state files in {dataset_id}", "INFO")
    return matching_files

def download_file(file_obj, output_dir, max_retries=MAX_RETRIES):
    """
    Download a single file from OpenNeuro.
    
    Args:
        file_obj: File object from get_dataset_files containing 'filename' and 'urls'
        output_dir: Directory to save the file
        max_retries: Maximum number of retry attempts
        
    Returns:
        Path: Path to the downloaded file
        
    Raises:
        requests.HTTPError: If download fails after all retries
    """
    filename = file_obj.get("filename")
    urls = file_obj.get("urls", [])
    
    if not urls:
        raise ValueError(f"No download URLs found for file: {filename}")
    
    # Try each URL until one works
    for url in urls:
        output_path = Path(output_dir) / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        for attempt in range(max_retries):
            try:
                log_event(f"Downloading {filename} (attempt {attempt + 1}/{max_retries})", "INFO")
                
                response = requests.get(url, stream=True, timeout=120)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                
                log_event(f"Downloaded {filename}: {downloaded / (1024*1024):.2f} MB", "INFO")
                return output_path
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    log_event(f"Failed to download {filename} after {max_retries} attempts: {e}", "ERROR")
                    raise
                log_event(f"Retry {attempt + 1}/{max_retries} for {filename}: {e}", "WARNING")
                time.sleep(RETRY_DELAY)
    
    raise requests.HTTPError(f"Failed to download {filename} after exhausting all URLs")

def compute_checksum(file_path, algorithm="md5"):
    """
    Compute checksum of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: md5)
        
    Returns:
        str: Hex digest of the file checksum
    """
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()

def verify_file_checksum(file_path, expected_checksum, algorithm="md5"):
    """
    Verify a file's checksum against an expected value.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected checksum value
        algorithm: Hash algorithm to use
        
    Returns:
        bool: True if checksum matches, False otherwise
    """
    if not os.path.exists(file_path):
        return False
    
    actual_checksum = compute_checksum(file_path, algorithm)
    return actual_checksum.lower() == expected_checksum.lower()

def save_checksums(checksums_dict, output_path):
    """
    Save checksums to a JSON file.
    
    Args:
        checksums_dict: Dictionary mapping filenames to checksums
        output_path: Path to save the checksums file
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(checksums_dict, f, indent=2)

def load_checksums(output_path):
    """
    Load checksums from a JSON file.
    
    Args:
        output_path: Path to the checksums file
        
    Returns:
        dict: Dictionary mapping filenames to checksums, or empty dict if file doesn't exist
    """
    if not os.path.exists(output_path):
        return {}
    
    with open(output_path, 'r') as f:
        return json.load(f)

def download_dataset(dataset_id=DATASET_ID, output_dir=OUTPUT_DIR):
    """
    Main function to download the ds000278 dataset.
    
    This function:
    1. Fetches dataset metadata
    2. Retrieves file list
    3. Identifies resting-state files
    4. Downloads each file
    5. Verifies checksums
    
    Args:
        dataset_id: OpenNeuro dataset identifier (default: ds000278)
        output_dir: Directory to download files to
        
    Returns:
        dict: Summary of download operation including success/failure counts
        
    Raises:
        FileNotFoundError: If required resting-state files are not found
        requests.HTTPError: If API calls fail
    """
    setup_logging()
    log_event(f"Starting download of dataset {dataset_id}", "INFO")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load existing checksums
    checksums_file = Path(output_dir) / CHECKSUM_FILE
    existing_checksums = load_checksums(checksums_file)
    
    # Get dataset metadata
    try:
        metadata = get_dataset_metadata(dataset_id)
        log_event(f"Dataset {dataset_id} found: {metadata.get('description', {}).get('Name', 'Unknown')}", "INFO")
    except requests.HTTPError as e:
        error_msg = f"Required resting-state dataset {dataset_id} not found. " \
                   f"OpenNeuro API error: {e}"
        log_event(error_msg, "ERROR")
        raise FileNotFoundError(error_msg)
    
    # Get file list
    try:
        file_list = get_dataset_files(dataset_id)
        log_event(f"Retrieved {len(file_list)} files from dataset", "INFO")
    except requests.HTTPError as e:
        error_msg = f"Failed to retrieve file list for {dataset_id}: {e}"
        log_event(error_msg, "ERROR")
        raise
    
    # Find resting-state files
    resting_state_files = find_resting_state_files(file_list, dataset_id)
    
    # Download files
    download_summary = {
        "dataset_id": dataset_id,
        "total_files": len(resting_state_files),
        "downloaded": 0,
        "skipped": 0,
        "failed": 0,
        "verified": 0,
        "failed_verification": 0,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    for file_obj in resting_state_files:
        filename = file_obj.get("filename")
        expected_checksum = file_obj.get("checksum", "")
        
        # Check if already downloaded and verified
        file_path = output_path / filename
        if file_path.exists() and filename in existing_checksums:
            if verify_file_checksum(file_path, existing_checksums[filename]):
                log_event(f"Skipping already downloaded and verified: {filename}", "INFO")
                download_summary["skipped"] += 1
                download_summary["verified"] += 1
                continue
            else:
                log_event(f"Checksum mismatch for existing file, re-downloading: {filename}", "WARNING")
        
        try:
            # Download file
            downloaded_path = download_file(file_obj, output_dir)
            download_summary["downloaded"] += 1
            
            # Verify checksum if available
            if expected_checksum:
                if verify_file_checksum(downloaded_path, expected_checksum):
                    download_summary["verified"] += 1
                    existing_checksums[filename] = expected_checksum
                    log_event(f"Checksum verified: {filename}", "INFO")
                else:
                    download_summary["failed_verification"] += 1
                    log_event(f"Checksum verification failed: {filename}", "ERROR")
            else:
                log_event(f"No checksum available for: {filename}", "WARNING")
                
        except Exception as e:
            download_summary["failed"] += 1
            log_event(f"Failed to download {filename}: {e}", "ERROR")
    
    # Save checksums
    save_checksums(existing_checksums, checksums_file)
    
    # Log summary
    log_event(f"Download summary: {download_summary}", "INFO")
    
    if download_summary["failed"] > 0 or download_summary["failed_verification"] > 0:
        log_event("Download completed with errors", "WARNING")
    else:
        log_event("Download completed successfully", "INFO")
    
    return download_summary

def main():
    """
    Main entry point for script execution.
    
    Downloads ds000278 dataset and exits with appropriate code.
    """
    try:
        result = download_dataset()
        
        # Exit with error if any files failed
        if result["failed"] > 0 or result["failed_verification"] > 0:
            sys.exit(1)
        
        sys.exit(0)
        
    except FileNotFoundError as e:
        log_event(str(e), "ERROR")
        sys.exit(1)
    except Exception as e:
        log_event(f"Unexpected error: {e}", "ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()
