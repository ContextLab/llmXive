"""
Standalone utility for verifying filtered dataset integrity.
Used by T040 to explicitly check SHA256 checksums against known-good values.
"""
import os
import sys
import hashlib
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_filtered_data_integrity(filtered_path: Path, checksums_file: Path) -> bool:
    """
    Verify the integrity of the filtered dataset by comparing its SHA256 checksum
    against a known-good checksum stored in the state file.

    Args:
        filtered_path: Path to the filtered dataset (data/filtered/...)
        checksums_file: Path to the state file containing known checksums

    Returns:
        bool: True if checksums match or if state file doesn't exist yet (first run),
              False if checksums mismatch.
    """
    if not filtered_path.exists():
        logger.error(f"Filtered dataset not found: {filtered_path}")
        return False

    if not checksums_file.exists():
        logger.warning(f"Checksum state file not found: {checksums_file}. Skipping integrity check (first run?).")
        return True

    try:
        import yaml
        with open(checksums_file, 'r') as f:
            state_data = yaml.safe_load(f)

        known_checksum = state_data.get('filtered_dataset_sha256')

        if known_checksum is None:
            logger.warning("No known checksum found in state file. Skipping integrity check.")
            return True

        actual_checksum = calculate_sha256(filtered_path)

        if actual_checksum != known_checksum:
            logger.error("CRITICAL: Filtered dataset integrity check FAILED!")
            logger.error(f"Expected checksum: {known_checksum}")
            logger.error(f"Actual checksum: {actual_checksum}")
            logger.error("The filtered dataset has changed since the last verified run.")
            return False

        logger.info(f"Filtered dataset integrity verified. Checksum: {actual_checksum}")
        return True

    except Exception as e:
        logger.error(f"Error during integrity verification: {e}")
        return False

def main():
    """Main entry point for integrity verification."""
    setup_logging()

    import argparse
    parser = argparse.ArgumentParser(description="Verify filtered dataset integrity")
    parser.add_argument("--filtered-file", default="data/filtered/edit-compass-filtered.json", help="Path to filtered dataset")
    parser.add_argument("--checksums-file", default="state/projects/PROJ-814-checksums.yaml", help="Path to checksums state file")
    args = parser.parse_args()

    filtered_path = Path(args.filtered_file)
    checksums_file = Path(args.checksums_file)

    if verify_filtered_data_integrity(filtered_path, checksums_file):
        logger.info("Integrity check passed.")
        sys.exit(0)
    else:
        logger.error("Integrity check failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
