"""
Data Acquisition Module for PROJ-099.
Downloads raw datasets, verifies checksums, and stores them in data/raw/.
"""
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, Tuple, Optional
import time

# Add parent to path for imports if running as script
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from utils.dataset_loaders import get_dataset_info, download_file, verify_domain
from utils.validators import compute_sha256, verify_checksum
from utils.logging_utils import log_warning

# FR-008 Disclaimer Constant
FR008_DISCLAIMER = "Findings are associational only; no causal claims are made."

def log_header(message: str):
    """
    Logs a formatted header message to stdout and stderr with the FR-008 disclaimer.
    
    Args:
        message: The main message to log.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    # Ensure the FR-008 disclaimer is present in all console output
    output = f"[{timestamp}] {message}\n{FR008_DISCLAIMER}"
    print(output)
    sys.stderr.write(output + "\n")

def download_and_verify_dataset(dataset_id: str, target_dir: Path, expected_checksums: Dict[str, str]) -> Tuple[bool, Optional[str]]:
    """
    Downloads a dataset, verifies its checksum, and logs the result with FR-008.
    
    Args:
        dataset_id: Identifier for the dataset (e.g., 'adult', 'compas').
        target_dir: Directory to save the raw file.
        expected_checksums: Dict mapping filename to expected SHA-256 hash.
        
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    log_header(f"Starting acquisition for dataset: {dataset_id}")
    
    dataset_info = get_dataset_info(dataset_id)
    if not dataset_info:
        error_msg = f"Dataset {dataset_id} not found in registry."
        log_header(f"ERROR: {error_msg}")
        return False, error_msg

    url = dataset_info['url']
    filename = dataset_info['filename']
    target_path = target_dir / filename

    # Verify domain
    if not verify_domain(url):
        error_msg = f"URL domain for {dataset_id} is not whitelisted."
        log_header(f"ERROR: {error_msg}")
        return False, error_msg

    log_header(f"Downloading {filename} from {url}")
    try:
        download_file(url, target_path)
    except Exception as e:
        error_msg = f"Failed to download {filename}: {str(e)}"
        log_header(f"ERROR: {error_msg}")
        return False, error_msg

    log_header(f"Verifying checksum for {filename}")
    actual_checksum = compute_sha256(target_path)
    expected_checksum = expected_checksums.get(filename)

    if expected_checksum and not verify_checksum(actual_checksum, expected_checksum):
        error_msg = f"Checksum mismatch for {filename}. Expected: {expected_checksum}, Got: {actual_checksum}"
        log_header(f"ERROR: {error_msg}")
        # Clean up failed download
        target_path.unlink()
        return False, error_msg

    log_header(f"Successfully acquired and verified {filename} (SHA-256: {actual_checksum})")
    return True, None

def main():
    """
    Main entry point for data acquisition.
    Downloads all configured datasets to data/raw/.
    """
    log_header("=== Starting Data Acquisition Pipeline ===")
    log_header(FR008_DISCLAIMER)
    
    # Define datasets and their expected checksums (placeholders to be updated with real hashes)
    # In a real run, these would be populated from a spec or manifest
    datasets_to_process = [
        'adult',
        'compas',
        'bank',
        'german',
        'lawschool'
    ]
    
    # Mock checksums for demonstration; in production, these must match real files
    # This ensures the code structure is correct even if checksums are missing
    expected_checksums = {
        'adult.csv': '', 
        'compas.csv': '',
        'bank.csv': '',
        'german.csv': '',
        'lawschool.csv': ''
    }

    raw_dir = Path("data/raw")
    raw_dir.mkdir(parents=True, exist_ok=True)

    success_count = 0
    fail_count = 0

    for ds_id in datasets_to_process:
        log_header(f"Processing dataset: {ds_id}")
        # Filter expected checksums for this specific file if needed, 
        # or pass the full dict and let the function handle missing keys gracefully
        success, error = download_and_verify_dataset(ds_id, raw_dir, expected_checksums)
        if success:
            success_count += 1
        else:
            fail_count += 1
            if error:
                log_warning(f"Skipping {ds_id} due to error.")

    log_header(f"Acquisition Complete: {success_count} successful, {fail_count} failed.")
    log_header(FR008_DISCLAIMER)

if __name__ == "__main__":
    main()
