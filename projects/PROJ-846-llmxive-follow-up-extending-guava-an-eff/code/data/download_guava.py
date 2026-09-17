"""
Download and verify the Guava dataset.

This script fetches the raw Guava dataset from Hugging Face,
computes checksums for integrity verification, and stores
them in a manifest file.

Raises:
    DatasetUnavailableError: If the dataset cannot be fetched or verified.
"""
import json
import os
import hashlib
import shutil
import tempfile
from pathlib import Path

# Import the specific exception defined in the project
from utils.exceptions import DatasetUnavailableError
from utils.config import ensure_directories

# Project root relative to the code directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "guava"
CHECKSUMS_FILE = RAW_DATA_DIR / "checksums.json"

# Hugging Face Dataset ID for Guava
# Using the official Guava dataset repository
DATASET_ID = "guava/dataset"
# Note: If the specific ID changes, this should be updated based on the
# verified real data source provided in the feedback loop.
# For now, we attempt to load the standard 'guava' dataset if available,
# or a specific variant. If the dataset is not public or requires auth,
# this will raise an error which is caught and re-raised as DatasetUnavailableError.
# Attempting to use a known public proxy or standard HF dataset structure.
# If 'guava/dataset' is not found, we try 'guava' directly.
HF_DATASET_NAME = "guava" 

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_guava_dataset(output_dir: Path) -> dict:
    """
    Download the Guava dataset to the specified output directory.

    Args:
        output_dir: Directory where the dataset will be saved.

    Returns:
        Dictionary mapping file paths to their SHA256 checksums.

    Raises:
        DatasetUnavailableError: If the dataset cannot be downloaded.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    checksums = {}

    try:
        # Attempt to load the dataset from Hugging Face
        # We use streaming=False to download the full dataset into memory/filesystem
        # to ensure we have the actual files to checksum.
        # Note: In a real execution environment, this requires internet access and the
        # dataset to be available.
        
        # Using the datasets library as per requirements.txt
        from datasets import load_dataset

        print(f"Attempting to load dataset: {HF_DATASET_NAME}...")
        
        # Try to load the dataset. If it fails, we raise an error.
        # We do NOT provide a synthetic fallback.
        try:
            dataset = load_dataset(HF_DATASET_NAME, split="train", cache_dir=str(output_dir))
        except Exception as load_err:
            # Try alternative loading if the primary name fails
            # Some datasets might be under a different ID or require specific config
            try:
                dataset = load_dataset(HF_DATASET_NAME, split="train")
            except Exception as alt_load_err:
                raise DatasetUnavailableError(
                    f"Failed to load Guava dataset from Hugging Face. "
                    f"Primary error: {load_err}. "
                    f"Alternative error: {alt_load_err}. "
                    f"Dataset may be private, renamed, or unavailable."
                )

        # The dataset is loaded. Now we need to extract files to disk to checksum them.
        # Hugging Face datasets often store data in memory or a cache.
        # We will iterate through the dataset and save representative files or the full structure.
        # For the purpose of this task, we will save the dataset to a specific format
        # and checksum the resulting files.
        
        # Create a subdirectory for the actual data files
        data_subdir = output_dir / "dataset_files"
        data_subdir.mkdir(exist_ok=True)

        # Save the dataset to parquet or jsonl for checksumming
        # This ensures we have physical files to hash
        data_path = data_subdir / "guava_data.jsonl"
        dataset.to_json(str(data_path))
        
        # Calculate checksum for the generated file
        file_hash = calculate_sha256(data_path)
        rel_path = str(data_path.relative_to(output_dir))
        checksums[rel_path] = file_hash

        print(f"Downloaded and checksummed: {rel_path}")

    except DatasetUnavailableError:
        # Re-raise our custom error
        raise
    except Exception as e:
        # Catch any other unexpected errors during download
        raise DatasetUnavailableError(
            f"Failed to download or process Guava dataset: {str(e)}"
        )

    return checksums

def main():
    """Main entry point for downloading the Guava dataset."""
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Target Directory: {RAW_DATA_DIR}")

    # Ensure directories exist
    ensure_directories([RAW_DATA_DIR])

    if CHECKSUMS_FILE.exists():
        print(f"Warning: Checksums file {CHECKSUMS_FILE} already exists.")
        overwrite = input("Overwrite? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("Exiting without download.")
            return

    try:
        print("Starting download of Guava dataset...")
        checksums = download_guava_dataset(RAW_DATA_DIR)

        # Write checksums to file
        with open(CHECKSUMS_FILE, 'w') as f:
            json.dump(checksums, f, indent=2)

        print(f"Successfully downloaded and verified dataset.")
        print(f"Checksums saved to: {CHECKSUMS_FILE}")

    except DatasetUnavailableError as e:
        print(f"CRITICAL ERROR: {e}")
        print("Dataset is unavailable. Cannot proceed without real data.")
        raise
    except Exception as e:
        print(f"Unexpected error during download: {e}")
        raise

if __name__ == "__main__":
    main()
