"""
Data download module for TransitLM dataset.
Handles fetching, streaming, checksum verification, and saving of the raw dataset.
"""

import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

# Ensure parent directory is in path for imports if run directly
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from datasets import load_dataset
except ImportError:
    print("Error: 'datasets' library is required. Install via: pip install datasets")
    sys.exit(1)

from config import Config, get_env_config


def compute_sha256(file_path: Path) -> str:
    """
    Computes the SHA256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def download_transitlm(output_dir: Optional[Path] = None, expected_sha256: Optional[str] = None) -> Path:
    """
    Downloads the TransitLM SFT dataset from Hugging Face using streaming.
    Applies SHA256 checksum verification if expected_sha256 is provided.
    Saves the dataset to a single JSON file.

    Args:
        output_dir: Directory to save the output. Defaults to data/raw/.
        expected_sha256: Expected SHA256 hash for verification. If None, skips verification.

    Returns:
        Path to the saved JSON file.

    Raises:
        ValueError: If the dataset download fails or checksum verification fails.
        RuntimeError: If the real data source cannot be accessed.
    """
    config = get_env_config()
    if output_dir is None:
        output_dir = Path(config.data_raw_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "transitlm_ground_truth.json"

    # If file exists and we are not forcing a re-download, we could check hash,
    # but per task requirements, we fetch and verify.
    # We will attempt to fetch the dataset.

    print(f"Starting download of TransitLM dataset to {output_file}...")
    print("Using streaming=True to handle large dataset efficiently.")

    dataset_id = "TransitLM/TransitLM-SFT" # Standard HF ID format, adjusting if specific subset needed

    try:
        # Load dataset with streaming to avoid downloading full GBs into memory first
        # We assume the dataset is a single config or we take the default split
        dataset = load_dataset(dataset_id, split="train", streaming=True)

        # Collect all data into a list of dicts for JSON serialization
        # Note: Streaming iterates, so we must materialize to write to a single JSON file
        # If the dataset is too large to fit in RAM, we should write line-by-line (JSONL)
        # However, the task specifies output: data/raw/transitlm_ground_truth.json
        # Standard JSON requires a list structure. If the dataset is huge, JSONL is safer.
        # Given the task explicitly asks for .json, we will attempt to write a JSON array.
        # If memory is a concern, we could switch to JSONL, but strict adherence to "transitlm_ground_truth.json"
        # suggests a standard JSON structure. Let's try to write it as a JSON array.
        
        # To prevent OOM on very large datasets, we will write incrementally if possible,
        # but standard json.dump requires an iterable.
        # We will iterate and write to a temporary file or handle chunking if needed.
        # For robustness with "real" large data, we will write as JSONL but name it .json if that's the spec,
        # OR better: write a valid JSON array by managing the file stream.
        
        # Strategy: Write opening bracket, then iterate and write objects with commas, then closing bracket.
        
        print(f"Fetching data from {dataset_id}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("[\n")
            first = True
            count = 0
            
            # Iterate through the streaming dataset
            for item in dataset:
                if not first:
                    f.write(",\n")
                else:
                    first = False
                
                # Ensure the item is serializable (handle potential numpy types if any)
                # Convert to standard python types if necessary
                json.dump(item, f, ensure_ascii=False)
                count += 1
                
                if count % 10000 == 0:
                    print(f"Processed {count} records...")

            f.write("\n]")
            print(f"Download complete. Total records: {count}")

    except Exception as e:
        # Fail loudly as per constraints
        raise RuntimeError(f"Failed to download or process real dataset from Hugging Face: {e}")

    # Verify checksum if provided
    if expected_sha256:
        print(f"Verifying SHA256 checksum for {output_file}...")
        actual_sha256 = compute_sha256(output_file)
        if actual_sha256 != expected_sha256:
            raise ValueError(
                f"SHA256 checksum mismatch!\n"
                f"Expected: {expected_sha256}\n"
                f"Actual:   {actual_sha256}"
            )
        print("Checksum verification passed.")
    else:
        print("Checksum verification skipped (no expected hash provided).")

    return output_file


def main():
    """
    Main entry point for the download script.
    """
    print("Running data/download.py")
    
    # Define expected hash if known, otherwise None
    # Since we don't have the hash pre-known in the prompt, we proceed without it
    # or allow the user to set it via env/config if needed.
    # For now, we assume no pre-known hash and just download.
    
    try:
        output_path = download_transitlm(expected_sha256=None)
        print(f"Successfully downloaded and saved to: {output_path}")
        
        # Basic sanity check
        if output_path.exists():
            size = output_path.stat().st_size
            print(f"File size: {size / (1024*1024):.2f} MB")
        else:
            raise RuntimeError("Output file was not created.")
            
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()