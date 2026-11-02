"""
Download and verify the Omni-Doc-1 TokenBench subset for the Qwen-Image-VAE-2.0 follow-up study.

This script fetches the dataset from the Hugging Face Hub, saves it as a Parquet file,
and records the download status and checksum for verification.
"""

import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, Any

from llmxive_toolkit import paths, get_logger
try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: 'datasets' library is required. Install with: pip install datasets")
    sys.exit(1)

log = get_logger(__name__)

# Configuration based on T006 specifications
DATASET_ID = "omnineura/Omni-Doc-1"
OUTPUT_FILE = paths.data("raw", "omnidoc_tokenbench.parquet")
STATUS_FILE = paths.data("raw", "download_status.json")
CHECKSUM_ALGO = "sha256"


def compute_file_checksum(filepath: Path, algorithm: str = "sha256") -> str:
    """Compute the checksum of a file."""
    hash_obj = hashlib.new(algorithm)
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def download_dataset() -> bool:
    """
    Fetch the Omni-Doc-1 dataset and save to disk.

    Returns:
        bool: True if successful.

    Raises:
        RuntimeError: If the download fails for any reason.
    """
    log.info(f"Attempting to load dataset: {DATASET_ID}")

    try:
        # Exact call specified in T006: split="train", streaming=False
        log.info("Fetching dataset from Hugging Face Hub (non-streaming)...")
        ds = load_dataset(DATASET_ID, split="train", streaming=False)
        
        num_rows = len(ds)
        log.info(f"Dataset loaded successfully. Number of rows: {num_rows}")

        # Save to Parquet
        log.info(f"Saving to {OUTPUT_FILE}...")
        ds.to_parquet(str(OUTPUT_FILE))
        log.info(f"Saved successfully to {OUTPUT_FILE}")

        # Compute checksum
        checksum = compute_file_checksum(OUTPUT_FILE, CHECKSUM_ALGO)
        log.info(f"Checksum ({CHECKSUM_ALGO}): {checksum}")

        # Write status report as required by T006
        status_data = {
            "success": True,
            "dataset_id": DATASET_ID,
            "file_path": str(OUTPUT_FILE),
            "checksum_algorithm": CHECKSUM_ALGO,
            "checksum": checksum,
            "num_rows": num_rows
        }

        with open(STATUS_FILE, "w") as f:
            json.dump(status_data, f, indent=2)
        
        log.info(f"Download status written to {STATUS_FILE}")
        return True

    except Exception as e:
        error_msg = f"Failed to download dataset {DATASET_ID}: {str(e)}"
        log.error(error_msg)
        
        # Write failure status to disk
        status_data = {
            "success": False,
            "error": error_msg
        }
        with open(STATUS_FILE, "w") as f:
            json.dump(status_data, f, indent=2)
          
        raise RuntimeError(error_msg) from e


def main() -> int:
    """Main entry point."""
    try:
        if download_dataset():
            log.info("Task T006 completed successfully.")
            return 0
        else:
            log.error("Task T006 failed.")
            return 1
    except Exception as e:
        log.exception(f"Task T006 failed with exception: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())