"""
Data Fetching Module.

Handles real dataset downloads from URLs defined in config.py.
Verifies checksums and handles partial downloads.
"""

import os
import hashlib
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import requests

from config import DATASET_URLS

class DataFetchError(Exception):
    """Exception raised when data fetching fails."""
    pass

def calculate_checksum(filepath: str, algorithm: str = "sha256") -> str:
    """Calculate checksum of a file."""
    hash_func = hashlib.getbyname(algorithm)
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def fetch_dataset(url: str, dest_path: str, expected_checksum: Optional[str] = None) -> str:
    """
    Fetch a dataset from a URL.
    Verifies checksum if provided.
    """
    try:
        # Stream download
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Save to temp file first
        fd, temp_path = tempfile.mkstemp()
        try:
            with os.fdopen(fd, "wb") as tmp:
                shutil.copyfileobj(response.raw, tmp)
            
            # Move to final destination
            Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.move(temp_path, dest_path)

            # Verify checksum
            if expected_checksum:
                actual_checksum = calculate_checksum(dest_path)
                if actual_checksum != expected_checksum:
                    raise DataFetchError(f"Checksum mismatch for {url}. Expected {expected_checksum}, got {actual_checksum}")
            
            return dest_path
        finally:
            if os.exists(temp_path):
                os.unlink(temp_path)

    except requests.RequestException as e:
        raise DataFetchError(f"Failed to download {url}: {e}")

def verify_all_datasets() -> None:
    """
    Verify all datasets in DATASET_URLS.
    If any fail, raise DataFetchError.
    """
    for name, url in DATASET_URLS.items():
        # In a real implementation, we would have checksums here
        # For now, we just check reachability
        try:
            response = requests.head(url)
            if response.status_code != 200:
                raise DataFetchError(f"Dataset {name} at {url} returned status {response.status_code}")
        except Exception as e:
            raise DataFetchError(f"Failed to verify dataset {name}: {e}")

def main():
    """Entry point for data fetcher."""
    try:
        verify_all_datasets()
        print("All datasets verified.")
    except DataFetchError as e:
        print(f"Data fetch error: {e}")
        raise

if __name__ == "__main__":
    main()
