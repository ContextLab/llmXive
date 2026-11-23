"""
Script to initialize the raw data manifest.

This is an alias or specific implementation for T006c requirements to ensure
manifest generation is robust. It duplicates logic from data_manifest_init.py
but focuses specifically on the raw directory.
"""
import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import RAW_DIR, MANIFEST_PATH
from utils.checksums import calculate_sha256
from utils.logging import setup_logger

logger = setup_logger("data_raw_manifest_init")

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def main():
    """Main entry point for raw manifest initialization."""
    raw_path = Path(RAW_DIR)
    manifest_path = Path(MANIFEST_PATH)
    
    if not raw_path.exists():
        logger.warning(f"Raw data directory {raw_path} does not exist.")
        return 1

    files = [f for f in raw_path.iterdir() if f.is_file() and f.name != ".gitkeep"]
    
    if not files:
        logger.warning(f"No files found in {raw_path} to hash.")
        # Create empty manifest if no files
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        return 0
    
    manifest_data = {}
    for f in files:
        logger.info(f"Hashing {f.name}...")
        manifest_data[f.name] = compute_file_hash(f)
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2)
    
    logger.info(f"Raw manifest updated at {manifest_path}.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
