"""
Environment configuration and dataset source verification.

This module handles:
- Environment variable checks
- Cache directory management
- Dataset path resolution
- Source integrity verification (URL and checksum)
- Loading verified datasets
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import hashlib
import json
import logging
from urllib.request import urlretrieve
from urllib.error import URLError, HTTPError

# Constants for the specific dataset
DATASET_ID = "materials-science/amorphous-silicon-shear-trajectories"
DATASET_URL_BASE = "https://huggingface.co/datasets/materials-science/amorphous-silicon-shear-trajectories/resolve/main"

# Configuration for verification
# In a real scenario, these would be fetched from a manifest or stored securely.
# For this implementation, we define the expected checksums for the primary shards.
# NOTE: These checksums are placeholders for the example. In production, they must match the actual file hashes.
EXPECTED_CHECKSUMS = {
    "shard_001.h5": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", # Example SHA-256
    "shard_002.h5": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
}

logger = logging.getLogger(__name__)

def check_environment_variable(var_name: str) -> bool:
    """Check if an environment variable is set and non-empty."""
    value = os.getenv(var_name)
    if value:
        logger.info(f"Environment variable {var_name} is set.")
        return True
    logger.warning(f"Environment variable {var_name} is not set or empty.")
    return False

def get_cache_dir() -> Path:
    """Return the cache directory path, creating it if necessary."""
    cache_base = os.getenv("LLMXIVE_CACHE_DIR", Path.home() / ".cache" / "llmXive")
    cache_path = Path(cache_base) / "datasets"
    cache_path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Cache directory set to: {cache_path}")
    return cache_path

def get_dataset_path() -> Path:
    """Return the specific dataset directory path."""
    cache_dir = get_cache_dir()
    # Sanitize dataset ID for filesystem usage
    safe_id = DATASET_ID.replace("/", "_")
    dataset_path = cache_dir / safe_id
    dataset_path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Dataset path set to: {dataset_path}")
    return dataset_path

def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute the hash of a file."""
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def verify_source_integrity(file_path: Path, expected_hash: str) -> bool:
    """
    Verify the integrity of a downloaded file against its expected checksum.
    
    Args:
        file_path: Path to the downloaded file.
        expected_hash: Expected SHA-256 hash string.
        
    Returns:
        True if the hash matches, False otherwise.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for integrity check: {file_path}")
    
    computed_hash = compute_file_hash(file_path)
    logger.info(f"Computed hash for {file_path.name}: {computed_hash}")
    logger.info(f"Expected hash: {expected_hash}")
    
    if computed_hash == expected_hash:
        logger.info(f"Integrity verification PASSED for {file_path.name}")
        return True
    else:
        logger.error(f"Integrity verification FAILED for {file_path.name}. Mismatch detected.")
        return False

def download_and_verify_shard(filename: str, expected_hash: str) -> Path:
    """
    Download a dataset shard and verify its integrity.
    
    Args:
        filename: Name of the file to download.
        expected_hash: Expected SHA-256 hash.
        
    Returns:
        Path to the verified file.
        
    Raises:
        URLError: If network access fails.
        ValueError: If integrity check fails.
    """
    dataset_path = get_dataset_path()
    file_path = dataset_path / filename
    url = f"{DATASET_URL_BASE}/{filename}"
    
    if file_path.exists():
        logger.info(f"File {filename} already exists. Verifying integrity...")
        if verify_source_integrity(file_path, expected_hash):
            return file_path
        else:
            logger.warning(f"Existing file {filename} failed integrity check. Re-downloading.")
            file_path.unlink()
    
    logger.info(f"Downloading {filename} from {url}...")
    try:
        urlretrieve(url, file_path)
    except (URLError, HTTPError) as e:
        logger.error(f"Failed to download {filename}: {e}")
        raise URLError(f"Failed to download dataset shard {filename}: {e}")
    
    logger.info(f"Download complete. Verifying integrity...")
    if not verify_source_integrity(file_path, expected_hash):
        raise ValueError(f"Integrity check failed for {filename}. The source may be corrupted or the expected hash is incorrect.")
    
    return file_path

def load_verified_dataset() -> Dict[str, Path]:
    """
    Ensure all required dataset shards are present and verified.
    
    Returns:
        Dictionary mapping shard names to their verified paths.
        
    Raises:
        ValueError: If any shard fails verification.
    """
    shards = {}
    for filename, expected_hash in EXPECTED_CHECKSUMS.items():
        try:
            path = download_and_verify_shard(filename, expected_hash)
            shards[filename] = path
        except Exception as e:
            logger.error(f"Failed to load shard {filename}: {e}")
            raise
    
    logger.info(f"Successfully loaded and verified {len(shards)} shards.")
    return shards

def get_dataset_config() -> Dict[str, Any]:
    """
    Return the configuration for the dataset source.
    
    Returns:
        Dictionary containing dataset metadata and configuration.
    """
    return {
        "id": DATASET_ID,
        "url_base": DATASET_URL_BASE,
        "expected_checksums": EXPECTED_CHECKSUMS,
        "cache_dir": str(get_cache_dir()),
        "dataset_dir": str(get_dataset_path()),
    }

def main():
    """CLI entry point for environment configuration and verification."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Verify dataset source configuration and integrity.")
    parser.add_argument("--verify", action="store_true", help="Download and verify dataset integrity.")
    parser.add_argument("--show-config", action="store_true", help="Print current configuration.")
    
    args = parser.parse_args()
    
    if args.show_config:
        config = get_dataset_config()
        print(json.dumps(config, indent=2))
        return
    
    if args.verify:
        try:
            shards = load_verified_dataset()
            print("Verification successful. Shards:")
            for name, path in shards.items():
                print(f"  {name}: {path}")
        except Exception as e:
            print(f"Verification failed: {e}")
            exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()