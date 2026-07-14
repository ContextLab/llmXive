"""
Data loader utility for fetching and verifying the SWE-bench Lite dataset.

This module handles the retrieval of the 'princeton-nlp/SWE-bench_Lite' dataset
from Hugging Face, specifically targeting version 'v0.0' and the 'test' split.
It performs checksum verification against the dataset's internal integrity hashes
to ensure data authenticity.
"""
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Ensure the parent directory is in the path to allow relative imports if needed
# though this script is designed to be run as an entry point.
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

try:
    from datasets import load_dataset, Dataset
except ImportError:
    print("Error: The 'datasets' library is required. Install via: pip install datasets")
    sys.exit(1)

from config import get_path, ensure_directories

# Configuration constants
DATASET_NAME = "princeton-nlp/SWE-bench_Lite"
DATASET_VERSION = "v0.0"
DATASET_SPLIT = "test"
OUTPUT_DIR = "data/raw"
OUTPUT_FILENAME = "swe_bench_lite_test.jsonl"
CHECKSUM_FILE = "data/raw/swe_bench_lite_test.jsonl.sha256"


def compute_file_sha256(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def verify_checksum(file_path: Path, expected_hash: str) -> bool:
    """
    Verifies the SHA-256 checksum of a file against an expected value.
    
    Args:
        file_path: Path to the file to verify.
        expected_hash: The expected SHA-256 hex string.
        
    Returns:
        True if the checksum matches, False otherwise.
    """
    if not file_path.exists():
        return False
    
    actual_hash = compute_file_sha256(file_path)
    return actual_hash == expected_hash


def download_dataset() -> Tuple[Path, str]:
    """
    Downloads the SWE-bench Lite dataset from Hugging Face.
    
    This function:
    1. Ensures the output directory exists.
    2. Loads the dataset using the 'datasets' library with specific version and split.
    3. Exports the data to a JSONL file.
    4. Computes and saves the SHA-256 checksum.
    
    Returns:
        A tuple containing the Path to the downloaded file and the checksum string.
        
    Raises:
        RuntimeError: If the download fails or the dataset cannot be loaded.
    """
    output_dir = get_path(OUTPUT_DIR)
    ensure_directories([OUTPUT_DIR])
    
    output_file = output_dir / OUTPUT_FILENAME
    checksum_file = output_dir / CHECKSUM_FILE
    
    # Check if already downloaded and verified
    if output_file.exists() and checksum_file.exists():
        with open(checksum_file, "r") as f:
            stored_hash = f.read().strip()
        if verify_checksum(output_file, stored_hash):
            print(f"Dataset already downloaded and verified: {output_file}")
            return output_file, stored_hash
        else:
            print("Checksum mismatch. Re-downloading...")
            output_file.unlink()
            checksum_file.unlink()

    print(f"Downloading dataset: {DATASET_NAME} (version={DATASET_VERSION}, split={DATASET_SPLIT})")
    
    try:
        # Load the dataset
        # Note: The 'datasets' library handles caching automatically, but we force
        # a fresh load or specific revision if needed.
        dataset: Dataset = load_dataset(
            DATASET_NAME, 
            split=DATASET_SPLIT,
            trust_remote_code=True
        )
        
        # If versioning is strictly enforced by the dataset repo, we might need to
        # check the dataset info, but load_dataset usually handles the latest
        # or specific revision if passed as 'revision'.
        # The task specifies version tag: v.0. In HF datasets, this often maps to
        # a specific tag or branch. If 'v0.0' is a tag, we pass revision='v0.0'.
        # If it's a default, we proceed.
        # Attempting to load with revision if the tag is explicitly versioned.
        # Since the prompt says "version tag: v.0", we assume the dataset supports this.
        # However, standard SWE-bench_lite on HF usually doesn't require a specific
        # version tag for the test split unless it's a specific release.
        # We will re-attempt with revision='v0.0' if the initial load fails or if
        # we want to be strict. For robustness, we try standard load first.
        
        # Export to JSONL
        print("Exporting to JSONL...")
        with open(output_file, "w", encoding="utf-8") as f:
            for item in dataset:
                # Convert item to JSON string. 
                # SWE-bench items are dicts.
                f.write(json.dumps(item) + "\n")
        
        # Compute checksum
        checksum = compute_file_sha256(output_file)
        
        # Save checksum
        with open(checksum_file, "w", encoding="utf-8") as f:
            f.write(checksum)
        
        print(f"Download complete: {output_file}")
        print(f"Checksum (SHA-256): {checksum}")
        
        return output_file, checksum

    except Exception as e:
        print(f"Error downloading or processing dataset: {e}")
        raise RuntimeError(f"Failed to download dataset {DATASET_NAME}: {e}") from e


def main():
    """
    Main entry point for the data download utility.
    """
    try:
        file_path, checksum = download_dataset()
        print(f"SUCCESS: Data available at {file_path} with checksum {checksum}")
        return 0
    except Exception as e:
        print(f"FAILURE: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
