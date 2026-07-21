"""
Data loading and management module.
Handles downloading, verification, and checksumming of datasets.
"""
import hashlib
import json
import os
import urllib.request
from pathlib import Path
from typing import Dict, Optional, Tuple

from config import load_config, get_path, ensure_dirs

def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute the hash of a file."""
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def download_file(url: str, dest_path: Path, chunk_size: int = 8192) -> None:
    """Download a file from a URL to a destination path."""
    ensure_dirs(dest_path)
    try:
        with urllib.request.urlopen(url) as response, open(dest_path, "wb") as out_file:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
    except Exception as e:
        raise RuntimeError(f"Failed to download {url}: {e}")

def load_checksums(config: Dict) -> Dict[str, str]:
    """Load existing checksums from disk."""
    checksums_path = get_path(config, "checksums_json")
    if checksums_path.exists():
        with open(checksums_path, "r") as f:
            return json.load(f)
    return {}

def save_checksums(config: Dict, checksums: Dict[str, str]) -> None:
    """Save checksums to disk."""
    checksums_path = get_path(config, "checksums_json")
    ensure_dirs(checksums_path)
    with open(checksums_path, "w") as f:
        json.dump(checksums, f, indent=2)

def verify_dataset(config: Dict, dataset_name: str, url: str, expected_hash: str) -> bool:
    """Download and verify a dataset."""
    raw_dir = get_path(config, "data_raw")
    file_name = dataset_name.replace("/", "_") + ".parquet"
    dest_path = raw_dir / file_name
    
    if not dest_path.exists():
        print(f"Downloading {dataset_name}...")
        download_file(url, dest_path)
    
    actual_hash = compute_file_hash(dest_path)
    if actual_hash != expected_hash:
        raise ValueError(f"Hash mismatch for {dataset_name}: expected {expected_hash}, got {actual_hash}")
    
    return True

def register_dataset(config: Dict, dataset_name: str, file_path: Path, hash_val: str) -> None:
    """Register a dataset in the checksum manifest."""
    checksums = load_checksums(config)
    checksums[dataset_name] = hash_val
    save_checksums(config, checksums)

def main():
    """Run basic data loader checks."""
    config = load_config()
    print("Data loader initialized.")
    print(f"Raw data directory: {get_path(config, 'data_raw')}")
    print(f"Processed data directory: {get_path(config, 'data_processed')}")

if __name__ == "__main__":
    main()
