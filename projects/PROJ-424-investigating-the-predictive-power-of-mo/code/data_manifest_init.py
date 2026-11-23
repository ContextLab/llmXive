"""
Script to initialize the data manifest.

This script ensures that the manifest.json file exists and contains
checksums for all files in the data/raw directory.
"""
import json
import os
import hashlib
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import RAW_DIR, MANIFEST_PATH
from utils.checksums import calculate_sha256
from utils.logging import setup_logger

logger = setup_logger("data_manifest_init")

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_gitkeep(path: Path):
    """Ensure .gitkeep exists in a directory."""
    gitkeep = path / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()
        logger.info(f"Created {gitkeep}")

def init_manifest():
    """Initialize the manifest file with checksums of all files in data/raw."""
    raw_path = Path(RAW_DIR)
    manifest_path = Path(MANIFEST_PATH)
    
    if not raw_path.exists():
        logger.warning(f"Raw data directory {raw_path} does not exist. Creating it.")
        raw_path.mkdir(parents=True, exist_ok=True)
    
    # Ensure .gitkeep
    ensure_gitkeep(raw_path)
    
    # Scan for files
    files = [f for f in raw_path.iterdir() if f.is_file() and f.name != ".gitkeep"]
    
    manifest_data = {}
    for f in files:
        logger.info(f"Hashing {f.name}...")
        manifest_data[f.name] = compute_file_hash(f)
    
    # Write manifest
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2)
    
    logger.info(f"Manifest initialized at {manifest_path} with {len(manifest_data)} files.")
    return manifest_data

def main():
    """Main entry point."""
    try:
        init_manifest()
        print("Manifest initialization complete.")
        return 0
    except Exception as e:
        logger.error(f"Failed to initialize manifest: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
