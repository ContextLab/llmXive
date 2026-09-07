"""
Download Guava dataset to data/raw/guava/ and generate checksums.json.
Raises DatasetUnavailableError if fetch fails. No synthetic fallback.
"""
import json
import os
import hashlib
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, List

# Import project utilities
from utils.exceptions import DatasetUnavailableError
from utils.config import ensure_directories

# Project root is assumed to be the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "guava"
CHECKSUMS_FILE = RAW_DATA_DIR / "checksums.json"

# The Guava dataset is available via Hugging Face Datasets
# Dataset ID: "guava-robotics/guava" (Example placeholder for real dataset lookup)
# Actual implementation will use the real dataset identifier once verified.
# For the purpose of this implementation, we assume the dataset is "guava-robotics/guava"
# and use the `datasets` library to stream/download it.
DATASET_ID = "guava-robotics/guava"
REVISION = "main"

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_guava_dataset() -> Dict[str, Any]:
    """
    Fetch raw Guava data from Hugging Face and save to data/raw/guava/.
    Returns a dictionary of file paths and their checksums.
    Raises DatasetUnavailableError if the dataset cannot be accessed.
    """
    ensure_directories([RAW_DATA_DIR])

    try:
        from datasets import load_dataset
    except ImportError:
        raise DatasetUnavailableError("The 'datasets' library is not installed. Please run 'pip install datasets'.")

    print(f"Attempting to download dataset: {DATASET_ID}")

    try:
        # Load the dataset in streaming mode to avoid downloading the entire thing into memory if not needed
        # However, for a raw data download task, we typically want to save the files.
        # We will iterate through the dataset and save the raw files (e.g., video frames, metadata)
        # The Guava dataset typically contains trajectories with images and actions.
        # We will save the raw parquet/arrow files or extract images if the dataset format requires it.
        
        # Strategy: Download the dataset to a temporary cache first, then move to RAW_DATA_DIR
        # Or stream and save files directly. Given the constraint of "raw data", we will
        # save the underlying data files if possible, or a representative sample if the full set is too large.
        # For this task, we assume we need the raw trajectory files.
        
        dataset = load_dataset(DATASET_ID, split="train", streaming=True)
        
        # Since streaming doesn't give us local file paths of the source easily for hashing,
        # and we need to store "raw" data, we will download the dataset to a temp dir,
        # calculate hashes, and then move to the final destination.
        # Note: For very large datasets, this might be memory/disk intensive.
        # We will assume a subset or the full dataset fits within the runner's constraints for this task.
        
        # Alternative: Use hf_hub_download if specific files are known.
        # Since the dataset structure might vary, we will use the `datasets` library's download mechanism.
        
        # Let's try to download the dataset to a temp directory first.
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Download the dataset to temp_dir
            # We use trust_remote_code=True if necessary, but usually not for standard datasets.
            ds = load_dataset(DATASET_ID, split="train", cache_dir=temp_path)
            
            # The `load_dataset` with cache_dir will store the data in a specific structure.
            # We need to find the actual data files (e.g., .parquet, .arrow, or image files).
            # Let's walk the temp_dir to find data files.
            
            data_files = []
            for root, dirs, files in os.walk(temp_path):
                for file in files:
                    if file.endswith(('.parquet', '.arrow', '.json', '.csv', '.jpg', '.png', '.mp4')):
                        full_path = Path(root) / file
                        # Skip hidden files or metadata files that aren't data
                        if not file.startswith('.'):
                            data_files.append(full_path)
            
            if not data_files:
                raise DatasetUnavailableError("No data files found in the downloaded dataset.")
            
            # Move data files to RAW_DATA_DIR
            print(f"Found {len(data_files)} data files. Moving to {RAW_DATA_DIR}...")
            
            checksums = {}
            for src_file in data_files:
                # Create relative path structure to preserve hierarchy or flatten?
                # Let's flatten to RAW_DATA_DIR for simplicity, or preserve structure.
                # We'll preserve the relative structure from the dataset's internal storage if possible,
                # but for simplicity in this task, we'll just copy the files with their original names
                # or a generated name if duplicates exist.
                
                dest_file = RAW_DATA_DIR / src_file.name
                # Handle duplicates if any
                counter = 1
                while dest_file.exists():
                    dest_file = RAW_DATA_DIR / f"{src_file.stem}_{counter}{src_file.suffix}"
                    counter += 1
                
                shutil.copy2(src_file, dest_file)
                
                # Calculate hash
                file_hash = calculate_sha256(dest_file)
                checksums[dest_file.name] = file_hash
                print(f"Downloaded and hashed: {dest_file.name} -> {file_hash}")
            
        return checksums

    except Exception as e:
        # Raise a specific error if the dataset is unavailable
        if "404" in str(e) or "not found" in str(e).lower():
            raise DatasetUnavailableError(f"Dataset {DATASET_ID} not found on Hugging Face. Error: {e}")
        elif "Connection" in str(e) or "timeout" in str(e):
            raise DatasetUnavailableError(f"Network error while fetching {DATASET_ID}. Please check your connection. Error: {e}")
        else:
            raise DatasetUnavailableError(f"Failed to download Guava dataset: {e}")

def main():
    """Main entry point for the download script."""
    print("Starting Guava dataset download...")
    
    try:
        checksums = download_guava_dataset()
        
        # Write checksums to JSON
        with open(CHECKSUMS_FILE, 'w') as f:
            json.dump(checksums, f, indent=2)
        
        print(f"Successfully downloaded Guava dataset to {RAW_DATA_DIR}")
        print(f"Checksums written to {CHECKSUMS_FILE}")
        print(f"Total files: {len(checksums)}")
        
    except DatasetUnavailableError as e:
        print(f"ERROR: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()