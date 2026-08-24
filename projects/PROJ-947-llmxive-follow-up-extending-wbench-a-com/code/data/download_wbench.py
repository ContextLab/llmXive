"""
WBench Dataset Downloader

Fetches the WBench dataset from the verified HuggingFace source.
This script strictly adheres to the 'no synthetic fallback' policy.
If the download fails, it raises an exception immediately.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from datasets import load_dataset
from utils.logging import get_logger, log_info, log_error, log_exception
from utils.errors import fail_loudly, SyntheticFallbackForbiddenError

# Configuration
# Verified source for WBench as per project specs
WBENCH_DATASET_ID = "wbench/wbench"
WBENCH_CONFIG = "default"
WBENCH_SPLIT = "train"

OUTPUT_DIR = Path(project_root) / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "wbench_raw.parquet"
CHECKSUM_FILE = Path(project_root) / "data" / "checksums.json"

logger = get_logger(__name__)

def ensure_output_directory():
    """Ensures the output directory exists."""
    if not OUTPUT_DIR.exists():
        log_info(f"Creating output directory: {OUTPUT_DIR}")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def download_wbench_dataset():
    """
    Downloads the WBench dataset from HuggingFace.
    
    Raises:
        Exception: If the download fails for any reason.
        SyntheticFallbackForbiddenError: If a fallback mechanism is attempted (prevented by design).
    """
    log_info(f"Starting download of dataset: {WBENCH_DATASET_ID}")
    
    try:
        # Load dataset with streaming=False to ensure full integrity check on download
        # We request the 'default' config. If the dataset has specific configs, 
        # this might need adjustment, but 'default' is the standard entry point.
        log_info("Fetching dataset from HuggingFace Hub...")
        dataset = load_dataset(
            WBENCH_DATASET_ID,
            name=WBENCH_CONFIG,
            split=WBENCH_SPLIT,
            trust_remote_code=True
        )
        
        log_info(f"Dataset loaded successfully. Number of rows: {len(dataset)}")
        
        # Save to parquet for efficient processing
        log_info(f"Saving dataset to {OUTPUT_FILE}")
        dataset.to_parquet(str(OUTPUT_FILE))
        
        if not OUTPUT_FILE.exists():
            fail_loudly("Downloaded file does not exist on disk.", logger)
        
        log_info("Download and save completed successfully.")
        return True

    except Exception as e:
        log_error(f"Failed to download WBench dataset: {str(e)}")
        log_exception(e)
        # Explicitly forbid any synthetic fallback logic here.
        # The error must propagate to the execution stage.
        raise SyntheticFallbackForbiddenError(
            f"Real data fetch failed. Synthetic fallback is forbidden. Error: {str(e)}"
        ) from e

def update_checksums():
    """
    Updates the checksums.json file with the hash of the newly downloaded file.
    """
    if not OUTPUT_FILE.exists():
        log_error("Cannot update checksums: Output file not found.")
        return

    from data.verify_checksums import compute_sha256
    
    file_hash = compute_sha256(OUTPUT_FILE)
    
    checksums = {}
    if CHECKSUM_FILE.exists():
        with open(CHECKSUM_FILE, 'r') as f:
            checksums = json.load(f)
    
    checksums["wbench_raw.parquet"] = file_hash
    
    with open(CHECKSUM_FILE, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    log_info(f"Updated checksum for wbench_raw.parquet: {file_hash}")

def main():
    """Main entry point for the download script."""
    log_info("=== Starting WBench Dataset Download ===")
    
    ensure_output_directory()
    
    success = download_wbench_dataset()
    
    if success:
        update_checksums()
        log_info("=== WBench Dataset Download Finished Successfully ===")
    else:
        fail_loudly("Download process did not complete successfully.", logger)

if __name__ == "__main__":
    main()