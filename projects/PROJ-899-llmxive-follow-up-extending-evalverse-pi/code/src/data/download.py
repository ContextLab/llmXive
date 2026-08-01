import hashlib
import os
import shutil
import sys
import tarfile
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

from src.config import get_raw_data_dir, get_cache_dir, DATASET_URL, DATASET_DOI

def ensure_directories():
    raw_dir = get_raw_data_dir()
    cache_dir = get_cache_dir()
    raw_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_stored_checksum(cache_file: Path) -> Optional[str]:
    if cache_file.exists():
        return cache_file.read_text().strip()
    return None

def save_checksum(checksum: str, cache_file: Path):
    cache_file.write_text(checksum)

def download_file(url: str, destination: Path) -> Path:
    if destination.exists():
        return destination
    print(f"Downloading {url} to {destination}...")
    try:
        urllib.request.urlretrieve(url, destination)
        return destination
    except Exception as e:
        raise RuntimeError(f"Failed to download dataset: {e}")

def extract_archive(archive_path: Path, destination: Path):
    print(f"Extracting {archive_path} to {destination}...")
    if archive_path.suffix == ".tar.gz":
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(destination)
    else:
        raise ValueError(f"Unsupported archive format: {archive_path.suffix}")

def is_data_available() -> bool:
    raw_dir = get_raw_data_dir()
    # Check for any content in raw directory
    return raw_dir.exists() and any(raw_dir.iterdir())

def fetch_evalverse_dataset():
    """
    Fetches the EvalVerse dataset from the configured URL.
    Handles download, checksum verification, and extraction.
    """
    ensure_directories()
    raw_dir = get_raw_data_dir()
    cache_dir = get_cache_dir()
    
    archive_name = "evalverse.tar.gz"
    archive_path = cache_dir / archive_name
    checksum_file = cache_dir / f"{archive_name}.sha256"
    
    # Download if not present
    if not archive_path.exists():
        download_file(DATASET_URL, archive_path)
    
    # Verify checksum (if available)
    if checksum_file.exists():
        stored_checksum = load_stored_checksum(checksum_file)
        current_checksum = compute_sha256(archive_path)
        if stored_checksum != current_checksum:
            print(f"Checksum mismatch! Expected {stored_checksum}, got {current_checksum}")
            # In a real scenario, we might re-download here
    
    # Extract if not already extracted
    if not is_data_available():
        extract_archive(archive_path, raw_dir)
        print("Dataset extracted successfully.")
    else:
        print("Dataset already available in raw directory.")

def main():
    fetch_evalverse_dataset()
    print("Dataset fetch complete.")

if __name__ == "__main__":
    main()
