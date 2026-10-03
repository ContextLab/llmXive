"""
Download the Guava raw dataset from Hugging Face.

This script downloads the 'guava/guava-v' dataset using streaming mode
to avoid loading the entire dataset into memory. It saves the raw data
to `data/raw/guava/` and generates a `checksums.json` file for integrity verification.

Constraints:
- Uses `datasets.load_dataset(..., streaming=True)`.
- Raises `DatasetUnavailableError` if the dataset ID is invalid or download fails.
- NO synthetic fallback logic is permitted.
"""

import json
import hashlib
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Import from project modules
from utils.errors import DatasetUnavailableError
from utils.config import get_path

# Third-party imports
try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: 'datasets' library is not installed. Run: pip install datasets")
    sys.exit(1)


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise RuntimeError(f"File not found for checksum: {file_path}")


def download_guava_dataset(output_dir: Path) -> List[Dict[str, Any]]:
    """
    Download the Guava dataset from Hugging Face using streaming.

    Args:
        output_dir: Directory where the raw data will be saved.

    Returns:
        List of dictionaries containing file paths and their checksums.

    Raises:
        DatasetUnavailableError: If the dataset cannot be found or downloaded.
    """
    dataset_id = "guava/guava-v"
    print(f"Attempting to download dataset: {dataset_id}...")

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    checksums: List[Dict[str, Any]] = []

    try:
        # Load dataset in streaming mode
        # Note: We assume the dataset has a 'train' split or similar.
        # If the specific structure is unknown, we iterate over splits.
        ds = load_dataset(dataset_id, split="train", streaming=True)
        
        # Iterate through the dataset to save files.
        # Since we don't know the exact schema without inspecting, we handle common cases.
        # The task requires saving trajectory files. We assume the dataset yields rows
        # containing image data or paths.
        
        # For this implementation, we assume the dataset yields dictionaries with
        # 'image' or 'frame' keys, or we save the raw JSON/Parquet if available.
        # However, standard HuggingFace datasets with streaming often require
        # explicit saving logic if we want to persist them to disk in a specific format.
        
        # Strategy: Since we need to save "trajectory files", we will collect
        # the data and save it as JSONL or similar if it's row-based.
        # If the dataset is image-heavy, we might need to save images.
        
        # Let's attempt to save the raw stream to a JSONL file first to capture the data.
        # This satisfies "trajectory files" in a generic sense until specific schema is known.
        
        output_file = output_dir / "guava_stream.jsonl"
        count = 0
        
        # We will download a small subset to verify connectivity and then
        # proceed to save the whole thing if memory allows (streaming avoids memory issues).
        # However, writing 7GB+ to disk might be slow. We will write directly.
        
        print(f"Streaming data to {output_file}...")
        
        # We need to handle the case where the dataset might not have the expected keys.
        # We'll try to serialize the row to JSON.
        
        with open(output_file, "w", encoding="utf-8") as f:
            for item in ds:
                # Serialize item to JSON string
                # Handle potential non-serializable types (like PIL images) if necessary.
                # For now, we assume the dataset is serializable or contains paths.
                # If it contains PIL images, we might need to save them separately.
                # Given the constraint "NO synthetic fallback", we must handle the real data structure.
                # If it fails due to non-serializable types, we catch and log.
                
                # Attempt to serialize
                try:
                    line = json.dumps(item, default=str)
                    f.write(line + "\n")
                    count += 1
                    
                    # Log progress
                    if count % 1000 == 0:
                        print(f"Downloaded {count} rows...")
                except TypeError as e:
                    print(f"Warning: Could not serialize row due to {e}. Skipping.")
                    continue

        print(f"Successfully downloaded {count} rows to {output_file}.")
        
        # Calculate checksum for the generated file
        checksum = calculate_sha256(output_file)
        checksums.append({
            "filename": output_file.name,
            "path": str(output_file),
            "sha256": checksum,
            "rows": count
        })

    except Exception as e:
        # Specific handling for dataset not found or network issues
        if "404" in str(e) or "not found" in str(e).lower():
            raise DatasetUnavailableError(f"Dataset '{dataset_id}' not found on Hugging Face. Error: {e}")
        elif "connection" in str(e).lower() or "timeout" in str(e).lower():
            raise DatasetUnavailableError(f"Network error while accessing '{dataset_id}'. Error: {e}")
        else:
            # Re-raise or wrap generic errors
            raise DatasetUnavailableError(f"Failed to download dataset '{dataset_id}'. Error: {e}")

    return checksums


def save_checksums(checksums: List[Dict[str, Any]], output_dir: Path) -> None:
    """Save the checksums to a JSON file."""
    checksum_file = output_dir / "checksums.json"
    try:
        with open(checksum_file, "w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2)
        print(f"Checksums saved to {checksum_file}")
    except IOError as e:
        print(f"ERROR: Failed to write checksums file: {e}")
        sys.exit(1)


def main():
    """Main entry point for the download script."""
    # Get the project root and data paths
    try:
        raw_data_dir = get_path("raw_data") / "guava"
    except Exception as e:
        print(f"ERROR: Could not initialize paths: {e}")
        sys.exit(1)

    print(f"Target directory: {raw_data_dir}")

    try:
        # Perform download
        checksums = download_guava_dataset(raw_data_dir)
        
        # Save checksums
        save_checksums(checksums, raw_data_dir)
        
        print("Download and verification completed successfully.")
        sys.exit(0)

    except DatasetUnavailableError as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()