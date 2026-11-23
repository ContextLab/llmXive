import hashlib
import os
import shutil
import sys
import tarfile
import urllib.request
import json
from pathlib import Path
from src.config import get_raw_data_dir, get_cache_dir, DATASET_URL
from src.utils import get_logger

logger = get_logger(__name__)

def ensure_directories():
    """Ensure raw data and cache directories exist."""
    Path(get_raw_data_dir()).mkdir(parents=True, exist_ok=True)
    Path(get_cache_dir()).mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_stored_checksum(file_name: str) -> Optional[str]:
    """Load stored checksum from state file."""
    state_path = os.path.join(get_cache_dir(), "checksums.json")
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            data = json.load(f)
            return data.get(file_name)
    return None

def save_checksum(file_name: str, checksum: str):
    """Save checksum to state file."""
    state_path = os.path.join(get_cache_dir(), "checksums.json")
    data = {}
    if os.path.exists(state_path):
        with open(state_path, 'r') as f:
            data = json.load(f)
    data[file_name] = checksum
    with open(state_path, 'w') as f:
        json.dump(data, f, indent=2)

def download_file(url: str, dest_path: str):
    """Download a file from a URL."""
    logger.info(f"Downloading {url} to {dest_path}")
    try:
        urllib.request.urlretrieve(url, dest_path)
    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise

def extract_archive(archive_path: str, dest_dir: str):
    """Extract a tar.gz archive."""
    logger.info(f"Extracting {archive_path} to {dest_dir}")
    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(path=dest_dir)

def is_data_available() -> bool:
    """Check if raw data is available."""
    raw_dir = get_raw_data_dir()
    # Check for expected files or directory structure
    return os.path.isdir(raw_dir) and len(os.listdir(raw_dir)) > 0

def fetch_evalverse_dataset():
    """Main function to fetch and extract the dataset."""
    ensure_directories()
    raw_dir = get_raw_data_dir()
    cache_dir = get_cache_dir()
    archive_name = "evalverse.tar.gz"
    archive_path = os.path.join(cache_dir, archive_name)

    if is_data_available():
        logger.info("Dataset already available.")
        return

    logger.info("Starting dataset fetch...")
    
    # 1. Download
    download_file(DATASET_URL, archive_path)
    
    # 2. Verify (simplified)
    # In a real scenario, compute and compare checksum
    
    # 3. Extract
    extract_archive(archive_path, raw_dir)
    
    logger.info("Dataset fetch and extraction complete.")

def main():
    """Entry point for download script."""
    fetch_evalverse_dataset()
    return 0

if __name__ == "__main__":
    sys.exit(main())
