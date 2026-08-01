"""
Data download and management utilities.
"""
import hashlib
import os
import shutil
import sys
import tarfile
import urllib.request
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

# Configuration constants (defined in T009b)
DATASET_DOI = "10.5281/zenodo.1234567"
DATASET_URL = "https://zenodo.org/api/records/1234567/files-archive"

def ensure_directories() -> None:
    """Ensure data directories exist."""
    from src.data.config import ensure_directories
    ensure_directories()

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_stored_checksum(checksum_file: Path) -> Optional[str]:
    """Load stored checksum from file."""
    if checksum_file.exists():
        return checksum_file.read_text().strip()
    return None

def save_checksum(checksum_file: Path, checksum: str) -> None:
    """Save checksum to file."""
    checksum_file.parent.mkdir(parents=True, exist_ok=True)
    checksum_file.write_text(checksum)

def download_file(url: str, destination: Path) -> Path:
    """Download a file from URL to destination."""
    ensure_directories()
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Downloading from {url}...")
    urllib.request.urlretrieve(url, destination)
    print(f"Downloaded to {destination}")
    return destination

def extract_archive(archive_path: Path, extract_to: Path) -> None:
    """Extract a tar.gz archive to a directory."""
    extract_to.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(path=extract_to)
    print(f"Extracted {archive_path} to {extract_to}")

def is_data_available() -> bool:
    """Check if the dataset is available locally."""
    from src.data.config import get_raw_data_path
    data_dir = get_raw_data_path()
    return data_dir.exists() and any(data_dir.iterdir())

def fetch_evalverse_dataset() -> None:
    """Fetch and extract the EvalVerse dataset."""
    from src.data.config import get_raw_data_path, get_cache_path
    
    ensure_directories()
    cache_dir = get_cache_path()
    raw_dir = get_raw_data_path()
    
    archive_path = cache_dir / "evalverse.tar.gz"
    
    if is_data_available():
        print("Dataset already available. Skipping download.")
        return
    
    # Download
    download_file(DATASET_URL, archive_path)
    
    # Verify checksum (if available)
    # For now, we proceed with extraction
    
    # Extract
    extract_archive(archive_path, raw_dir)
    
    # Clean up archive
    if archive_path.exists():
        archive_path.unlink()
        print("Cleaned up archive file.")

def main():
    """Main entry point for dataset fetching."""
    fetch_evalverse_dataset()
