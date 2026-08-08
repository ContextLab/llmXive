import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import get_processed_data_dir, get_data_dir
from logging_config import setup_logging, get_logger

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_existing_checksums(checksums_path: Path) -> Dict[str, Any]:
    """Load existing checksums JSON or return empty dict if not exists."""
    if not checksums_path.exists():
        return {}
    with open(checksums_path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_checksums(checksums_path: Path, checksums: Dict[str, Any]) -> None:
    """Save checksums dictionary to JSON file."""
    with open(checksums_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)

def main() -> int:
    """
    Compute SHA-256 checksum for data/processed/anonymised_ratings.csv
    and record it in data/checksums.json.
    """
    setup_logging()
    logger = get_logger(__name__)

    # Define paths
    data_dir = get_data_dir()
    processed_dir = get_processed_data_dir()
    checksums_path = data_dir / "checksums.json"
    target_file = processed_dir / "anonymised_ratings.csv"

    # Verify target file exists
    if not target_file.exists():
        logger.error(f"Target file not found: {target_file}")
        print(f"Error: {target_file} does not exist. Cannot compute checksum.")
        return 1

    logger.info(f"Computing SHA-256 for: {target_file}")

    # Compute hash
    file_hash = compute_sha256(target_file)
    logger.info(f"Computed hash: {file_hash}")

    # Load existing checksums
    existing_checksums = load_existing_checksums(checksums_path)

    # Update or add entry for the target file
    relative_path = str(target_file.relative_to(data_dir.parent))
    existing_checksums[relative_path] = {
        "sha256": file_hash,
        "algorithm": "SHA-256",
        "status": "verified"
    }

    # Save updated checksums
    save_checksums(checksums_path, existing_checksums)
    logger.info(f"Checksum recorded in {checksums_path}")

    print(f"Successfully computed and recorded SHA-256 for {relative_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
