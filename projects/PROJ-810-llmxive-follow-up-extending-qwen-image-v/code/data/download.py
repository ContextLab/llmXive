"""
Download and verify the OmniDoc-TokenBench dataset for the Qwen-Image-VAE-2.0 follow-up study.

This script fetches the 'omnidoc-tokenbench' subset from the Hugging Face Hub,
saves it as a Parquet file, and computes a SHA-256 checksum for verification.
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

# Configuration
DATASET_ID = "omnidoc/omnidoc-tokenbench"
SUBSET_NAME = "omnidoc-tokenbench"  # The specific subset mentioned in the report
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "omnidoc_tokenbench.parquet"
CHECKSUM_OUTPUT = Path("data/results/checksum.json")
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
    Fetch the OmniDoc-TokenBench dataset and save to disk.

    Raises:
        FileNotFoundError: If the specific subset ID is not found on the Hub.
        RuntimeError: If the download fails for other reasons.
    """
    print(f"Attempting to load dataset: {DATASET_ID} (subset: {SUBSET_NAME})")

    # Ensure output directories exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKSUM_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Load the dataset. We use streaming=False to ensure we get the full data for the parquet file,
        # but we handle potential errors if the subset doesn't exist.
        # The 'split' argument is often 'train' or 'test' in these datasets, but if the config is the subset,
        # we try loading the config directly.
        # Based on common HuggingFace patterns for 'subset' references, it often maps to 'config_name'.
        print("Fetching dataset metadata...")
        ds = load_dataset(DATASET_ID, name=SUBSET_NAME, split="train")
        
        print(f"Dataset loaded successfully. Number of rows: {len(ds)}")
        print(f"Features: {ds.features}")

        # Save to Parquet
        print(f"Saving to {OUTPUT_FILE}...")
        # To_parquet is available on Dataset objects
        ds.to_parquet(str(OUTPUT_FILE))
        print(f"Saved successfully to {OUTPUT_FILE}")

        # Compute checksum
        checksum = compute_file_checksum(OUTPUT_FILE, CHECKSUM_ALGO)
        print(f"Checksum ({CHECKSUM_ALGO}): {checksum}")

        # Write checksum report
        checksum_data = {
            "dataset_id": DATASET_ID,
            "subset": SUBSET_NAME,
            "file_path": str(OUTPUT_FILE),
            "checksum_algorithm": CHECKSUM_ALGO,
            "checksum_value": checksum,
            "num_rows": len(ds),
            "status": "success"
        }

        with open(CHECKSUM_OUTPUT, "w") as f:
            json.dump(checksum_data, f, indent=2)
        
        print(f"Checksum report written to {CHECKSUM_OUTPUT}")
        return True

    except FileNotFoundError as e:
        # This is the specific error HuggingFace raises if the config/subset doesn't exist
        error_msg = (
            f"CRITICAL ERROR: The specified subset '{SUBSET_NAME}' was not found "
            f"in dataset '{DATASET_ID}'. "
            f"Please verify the dataset ID and subset name from the Qwen-Image-VAE-2.0 report. "
            f"Original error: {str(e)}"
        )
        print(error_msg)
        
        # Write an error artifact as requested by the task constraints
        error_report = {
            "dataset_id": DATASET_ID,
            "subset": SUBSET_NAME,
            "status": "failed",
            "error_type": "subset_not_found",
            "message": error_msg
        }
        CHECKSUM_OUTPUT.write_text(json.dumps(error_report, indent=2))
        raise FileNotFoundError(error_msg) from e
    except Exception as e:
        error_msg = f"Failed to download dataset: {str(e)}"
        print(error_msg)
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
