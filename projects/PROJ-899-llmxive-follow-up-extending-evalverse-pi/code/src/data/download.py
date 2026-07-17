"""
Download and cache the EvalVerse dataset.

This module handles fetching the EvalVerse dataset from Zenodo and extracting
it to the local cache directory. It ensures that data is only downloaded once
and reused on subsequent runs.

The dataset is fetched from Zenodo record 13130186 (EvalVerse: A Large-Scale
Dataset for Evaluating Video-Language Models).
"""

import hashlib
import os
import shutil
import sys
import tarfile
import urllib.request
from pathlib import Path
from typing import Optional

# Constants
ZENODO_RECORD_ID = "13130186"
ZENODO_FILE_ID = "13130187"  # The specific file ID for the dataset archive
# The actual download URL pattern for Zenodo files
ZENODO_BASE_URL = f"https://zenodo.org/records/{ZENODO_RECORD_ID}/files"

# Expected filename in the archive (may vary, but this is the standard name)
EXPECTED_ARCHIVE_NAME = "evalverse_dataset.tar.gz"

# Local paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
CACHE_DIR = PROJECT_ROOT / "data" / "cache"
CHECKSUM_FILE = PROJECT_ROOT / "state" / "evalverse_checksum.txt"

# Expected SHA-256 hash of the downloaded archive (will be updated after first download)
# For now, we compute it on the fly and store it
EXPECTED_SHA256 = None  # Will be computed and stored after first successful download


def ensure_directories() -> None:
    """Create necessary directories if they don't exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "state").mkdir(parents=True, exist_ok=True)


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def load_stored_checksum() -> Optional[str]:
    """Load the previously stored checksum if it exists."""
    if CHECKSUM_FILE.exists():
        return CHECKSUM_FILE.read_text().strip()
    return None


def save_checksum(checksum: str) -> None:
    """Save the checksum to disk."""
    CHECKSUM_FILE.write_text(checksum)


def download_file(url: str, destination: Path) -> None:
    """Download a file from a URL with progress reporting."""
    print(f"Downloading from {url}...")
    try:
        # Use a larger block size for efficiency
        block_size = 1024 * 1024  # 1MB
        with urllib.request.urlopen(url) as response, open(destination, "wb") as out_file:
            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0
            while True:
                chunk = response.read(block_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    progress = (downloaded / total_size) * 100
                    print(f"\rProgress: {progress:.2f}% ({downloaded / (1024*1024):.2f} MB / {total_size / (1024*1024):.2f} MB)", end="")
                else:
                    print(f"\rDownloaded: {downloaded / (1024*1024):.2f} MB", end="")
        print()  # New line after progress
    except Exception as e:
        raise RuntimeError(f"Failed to download file from {url}: {e}")


def extract_archive(archive_path: Path, extract_to: Path) -> None:
    """Extract a tar.gz archive to the specified directory."""
    print(f"Extracting {archive_path} to {extract_to}...")
    try:
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=extract_to)
        print("Extraction complete.")
    except Exception as e:
        raise RuntimeError(f"Failed to extract archive: {e}")


def is_data_available() -> bool:
    """Check if the raw data directory contains expected files."""
    # Check if the raw directory has any content (assuming the dataset creates files)
    if not DATA_RAW_DIR.exists():
        return False
    
    # List contents to verify something is there
    contents = list(DATA_RAW_DIR.iterdir())
    if not contents:
        return False
    
    # Optional: Check for specific expected files if known
    # For now, we assume if there's content, it's valid
    return True


def fetch_evalverse_dataset() -> None:
    """
    Fetch the EvalVerse dataset from Zenodo if not already cached.
    
    This function:
    1. Checks if data is already available in data/raw/
    2. If not, downloads the dataset from Zenodo
    3. Extracts the archive to data/raw/
    4. Computes and stores the checksum for verification
    """
    ensure_directories()
    
    # Check if data is already available
    if is_data_available():
        print("EvalVerse dataset already exists in data/raw/. Skipping download.")
        return
    
    # Construct the download URL
    # Zenodo typically provides a direct download link like:
    # https://zenodo.org/records/{record_id}/files/{file_id}
    # But we need to get the actual file name first.
    # For EvalVerse, the dataset is typically a single tar.gz file.
    
    # The actual file URL pattern for Zenodo records
    # We'll use the API to get the file info or construct the URL directly
    # For simplicity, we'll assume the file is named evalverse_dataset.tar.gz
    # and use the direct download URL pattern.
    
    # Note: The actual file ID might need to be adjusted based on Zenodo's structure
    # For EvalVerse (record 13130186), the main dataset file is typically the first one.
    # We'll construct the URL assuming the file is accessible via the records API.
    
    # Alternative approach: Use the Zenodo API to get the file URL
    # But for simplicity, we'll try the direct download URL pattern.
    
    # The actual download URL for the file
    # This is a placeholder - the actual URL might need adjustment
    download_url = f"{ZENODO_BASE_URL}/evalverse_dataset.tar.gz"
    
    # If the above doesn't work, we might need to use the API:
    # https://zenodo.org/api/records/{record_id}
    # to get the actual file URL.
    
    # For now, let's try a more robust approach using the Zenodo API
    import json
    
    try:
        # Get record info from Zenodo API
        api_url = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}"
        with urllib.request.urlopen(api_url) as response:
            record_info = json.loads(response.read().decode())
        
        # Find the file with the dataset
        files = record_info.get("files", [])
        if not files:
            raise RuntimeError("No files found in Zenodo record.")
        
        # Find the tar.gz file (or the first file if only one)
        dataset_file = None
        for file_info in files:
            if file_info.get("key", "").endswith(".tar.gz") or file_info.get("key", "").endswith(".zip"):
                dataset_file = file_info
                break
        
        if not dataset_file:
            # If no compressed file found, use the first file
            dataset_file = files[0]
        
        # Get the actual download URL
        download_url = dataset_file["links"]["self"]
        expected_filename = dataset_file["key"]
        
    except Exception as e:
        raise RuntimeError(f"Failed to fetch file information from Zenodo API: {e}")
    
    # Download the file
    archive_path = CACHE_DIR / expected_filename
    download_file(download_url, archive_path)
    
    # Compute and store checksum
    checksum = compute_sha256(archive_path)
    print(f"Downloaded file checksum: {checksum}")
    save_checksum(checksum)
    
    # Extract the archive
    extract_archive(archive_path, DATA_RAW_DIR)
    
    # Clean up the archive if desired (optional)
    # archive_path.unlink()
    
    print(f"EvalVerse dataset successfully downloaded and extracted to {DATA_RAW_DIR}")


def main() -> None:
    """Main entry point for the download script."""
    try:
        fetch_evalverse_dataset()
        print("Download process completed successfully.")
        sys.exit(0)
    except Exception as e:
        print(f"Download process failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
