"""
code/setup_data_dirs.py

Implements T011: Setup data directories and checksumming hooks.
Ensures data/raw/ and data/derived/ exist and are writable.
"""
import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ensure_directories(base_path: Path) -> None:
    """Ensure required directories exist."""
    dirs_to_create = [
        base_path / "data" / "raw",
        base_path / "data" / "derived",
        base_path / "state",
        base_path / "state" / "hashes"
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        # Check writability
        test_file = dir_path / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
            logger.info(f"Directory {dir_path} is writable.")
        except OSError as e:
            logger.error(f"Directory {dir_path} is not writable: {e}")
            raise

def get_data_files(root_path: Path) -> List[Path]:
    """Get all files in data/ directory."""
    data_path = root_path / "data"
    files = []
    if data_path.exists() and data_path.is_dir():
        for file_path in data_path.rglob("*"):
            if file_path.is_file():
                files.append(file_path)
    return files

def generate_checksums(root_path: Path) -> Dict[str, str]:
    """Generate checksums for all data files."""
    files = get_data_files(root_path)
    checksums = {}
    
    for file_path in files:
        rel_path = str(file_path.relative_to(root_path))
        file_hash = calculate_sha256(str(file_path))
        checksums[rel_path] = file_hash
    
    return checksums

def save_checksums(root_path: Path, checksums: Dict[str, str]) -> None:
    """Save checksums to a JSON file."""
    checksum_path = root_path / "state" / "data_checksums.json"
    with open(checksum_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)
    logger.info(f"Checksums saved to {checksum_path}")

def main():
    """Main entry point."""
    root_path = Path(__file__).resolve().parent.parent
    
    logger.info(f"Setting up data directories in {root_path}")
    ensure_directories(root_path)
    
    checksums = generate_checksums(root_path)
    save_checksums(root_path, checksums)
    
    logger.info("Data directory setup complete.")

if __name__ == "__main__":
    main()