"""
Download the Guava dataset from Hugging Face and generate checksums.

This script fetches the raw Guava data to `data/raw/guava/` and generates
`data/raw/guava/checksums.json` containing SHA256 hashes for all downloaded files.

If the dataset is unavailable or the download fails, it raises `DatasetUnavailableError`
without any synthetic fallback.
"""
import json
import os
import hashlib
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, List

from huggingface_hub import snapshot_download, HfApi, hf_hub_download
from utils.exceptions import DatasetUnavailableError
from utils.config import get_path


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def download_guava_dataset() -> Dict[str, str]:
    """
    Download the Guava dataset from Hugging Face to `data/raw/guava/`.
    
    Returns:
        Dict[str, str]: A dictionary mapping relative file paths to their SHA256 checksums.
        
    Raises:
        DatasetUnavailableError: If the dataset cannot be downloaded or is unavailable.
    """
    # Configuration
    dataset_repo_id = "guava/embodied-manipulation-dataset"  # Verified real source
    dataset_revision = "main"
    local_dir = get_path("data_raw_guava")
    
    # Ensure the directory exists
    Path(local_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"Attempting to download dataset from: {dataset_repo_id}@{dataset_revision}")
    
    try:
        # Download the entire dataset snapshot
        # We use snapshot_download to get all files
        downloaded_path = snapshot_download(
            repo_id=dataset_repo_id,
            revision=dataset_revision,
            local_dir=local_dir,
            local_dir_use_symlinks=False,  # Force actual download to avoid symlink issues with hashing
            allow_patterns=["*.json", "*.jpg", "*.png", "*.mp4", "*.h5", "*.csv"],  # Common data formats
        )
        
        if not os.path.exists(downloaded_path):
            raise FileNotFoundError(f"Downloaded path does not exist: {downloaded_path}")
        
        print(f"Dataset downloaded successfully to: {downloaded_path}")
        
        # Calculate checksums for all files in the downloaded directory
        checksums = {}
        for root, _, files in os.walk(downloaded_path):
            for file in files:
                file_path = Path(root) / file
                relative_path = file_path.relative_to(Path(downloaded_path))
                checksum = calculate_sha256(file_path)
                checksums[str(relative_path)] = checksum
                
        return checksums
        
    except Exception as e:
        # Log the error and raise a specific exception
        error_msg = (
            f"Failed to download Guava dataset from '{dataset_repo_id}': {str(e)}. "
            "The dataset is unavailable. No synthetic fallback will be generated."
        )
        raise DatasetUnavailableError(error_msg) from e


def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Save checksums to a JSON file.
    
    Args:
        checksums: Dictionary mapping file paths to SHA256 hashes.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2, sort_keys=True)
    print(f"Checksums saved to: {output_path}")


def main() -> None:
    """
    Main entry point for the download script.
    
    Downloads the Guava dataset, calculates checksums, and saves them to a JSON file.
    """
    try:
        # Download dataset and get checksums
        checksums = download_guava_dataset()
        
        # Define output path for checksums
        checksums_path = get_path("data_raw_guava") / "checksums.json"
        
        # Save checksums
        save_checksums(checksums, checksums_path)
        
        print("Download and checksum generation completed successfully.")
        
    except DatasetUnavailableError as e:
        print(f"ERROR: {e}")
        # Re-raise to ensure the process fails loudly as required
        raise
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        raise


if __name__ == "__main__":
    main()