import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import get_raw_data_dir, get_data_dir
from logging_config import setup_logging, get_logger

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_existing_checksums(checksums_path: Path) -> Dict[str, str]:
    """Load existing checksums from JSON file."""
    if not checksums_path.exists():
        return {}
    with open(checksums_path, "r") as f:
        return json.load(f)

def save_checksums(checksums_path: Path, checksums: Dict[str, str]) -> None:
    """Save checksums to JSON file."""
    with open(checksums_path, "w") as f:
        json.dump(checksums, f, indent=2)

def main() -> int:
    """Main entry point for computing checksums."""
    logger = setup_logging()
    logger.info("Starting checksum computation for real_ratings.csv")

    raw_data_dir = get_raw_data_dir()
    checksums_path = get_data_dir() / "checksums.json"
    target_file = raw_data_dir / "real_ratings.csv"

    if not target_file.exists():
        logger.error(f"Target file not found: {target_file}")
        print(f"Error: Target file not found: {target_file}", file=sys.stderr)
        return 1

    # Load existing checksums
    existing_checksums = load_existing_checksums(checksums_path)

    # Compute new checksum
    checksum = compute_sha256(target_file)
    relative_path = str(target_file.relative_to(get_data_dir().parent))

    # Update checksums dictionary
    existing_checksums[relative_path] = checksum

    # Save updated checksums
    save_checksums(checksums_path, existing_checksums)

    logger.info(f"Checksum computed for {relative_path}: {checksum}")
    logger.info(f"Checksums saved to {checksums_path}")
    print(f"Checksum for {relative_path}: {checksum}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
