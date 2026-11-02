"""
Download and verify the Omni-Doc-1 TokenBench subset for the Qwen-Image-VAE-2.0 follow-up study.

This script fetches the dataset from the Hugging Face Hub, saves it as a Parquet file,
and records the download status and checksum for verification.
"""

import hashlib
import json
import os
import sys
from pathlib import Path

# Add project root to path to ensure imports work if run as script
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: 'datasets' library is required. Install with: pip install datasets")
    sys.exit(1)

# Configuration based on T006 specifications
DATASET_ID = "omnineura/Omni-Doc-1"
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "omnidoc_tokenbench.parquet"
STATUS_FILE = OUTPUT_DIR / "download_status.json"
CHECKSUM_ALGO = "sha256"


def compute_file_checksum(filepath: Path, algorithm: str = "sha256") -> str:
    """Compute the checksum of a file."""
    hash_obj = hashlib.new(algorithm)
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def download_dataset():
    """
    Fetch the Omni-Doc-1 dataset and save to disk.

    Raises:
        RuntimeError: If the download fails for any reason.
    """
    print(f"Attempting to load dataset: {DATASET_ID}")

    # Ensure output directories exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Exact call specified in T006
        print("Fetching dataset from Hugging Face Hub...")
        ds = load_dataset(DATASET_ID, split="train", streaming=False)
        
        print(f"Dataset loaded successfully. Number of rows: {len(ds)}")

        # Save to Parquet
        print(f"Saving to {OUTPUT_FILE}...")
        ds.to_parquet(str(OUTPUT_FILE))
        print(f"Saved successfully to {OUTPUT_FILE}")

        # Compute checksum
        checksum = compute_file_checksum(OUTPUT_FILE, CHECKSUM_ALGO)
        print(f"Checksum ({CHECKSUM_ALGO}): {checksum}")

        # Write status report as required by T006
        status_data = {
            "success": True,
            "dataset_id": DATASET_ID,
            "file_path": str(OUTPUT_FILE),
            "checksum_algorithm": CHECKSUM_ALGO,
            "checksum": checksum,
            "num_rows": len(ds)
        }

        with open(STATUS_FILE, "w") as f:
            json.dump(status_data, f, indent=2)
        
        print(f"Download status written to {STATUS_FILE}")
        return True

    except Exception as e:
        error_msg = f"Failed to download dataset {DATASET_ID}: {str(e)}"
        print(error_msg)
        
        # Write failure status to disk
        status_data = {
            "success": False,
            "error": error_msg
        }
        with open(STATUS_FILE, "w") as f:
            json.dump(status_data, f, indent=2)
            
        raise RuntimeError(error_msg) from e


def main():
    """Main entry point."""
    try:
        success = download_dataset()
        if success:
            print("Task T006 completed successfully.")
            return 0
        else:
            print("Task T006 failed.")
            return 1
    except Exception as e:
        print(f"Task T006 failed with exception: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())