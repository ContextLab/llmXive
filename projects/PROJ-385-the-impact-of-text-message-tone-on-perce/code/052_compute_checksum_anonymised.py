"""
Task T052: Compute SHA-256 checksum for data/processed/anonymised_ratings.csv
and record it in data/checksums.json.
"""
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Import project configuration and logging utilities
from config import get_processed_data_dir, get_data_dir
from logging_config import setup_logging, get_logger


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error computing checksum for {file_path}: {e}")


def load_existing_checksums(checksum_file: Path) -> Dict[str, Any]:
    """Load existing checksums from JSON file."""
    if not checksum_file.exists():
        return {}
    try:
        with open(checksum_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logging.warning(f"Checksum file {checksum_file} is not valid JSON. Starting fresh.")
        return {}
    except Exception as e:
        raise RuntimeError(f"Error loading checksums from {checksum_file}: {e}")


def save_checksums(checksums: Dict[str, Any], checksum_file: Path) -> None:
    """Save checksums to JSON file."""
    try:
        with open(checksum_file, "w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2)
    except Exception as e:
        raise RuntimeError(f"Error saving checksums to {checksum_file}: {e}")


def main() -> int:
    """Main entry point for T052."""
    setup_logging()
    logger = get_logger(__name__)

    # Define paths
    data_dir = get_data_dir()
    processed_dir = get_processed_data_dir()
    checksum_file = data_dir / "checksums.json"
    target_file = processed_dir / "anonymised_ratings.csv"

    logger.info(f"Task T052: Computing checksum for {target_file}")

    # Verify input file exists
    if not target_file.exists():
        logger.error(f"Required file not found: {target_file}")
        logger.error("This task depends on T051 (anonymisation) completing successfully.")
        return 1

    # Compute checksum
    try:
        checksum = compute_sha256(target_file)
        logger.info(f"Computed SHA-256: {checksum}")
    except Exception as e:
        logger.error(f"Failed to compute checksum: {e}")
        return 1

    # Load existing checksums
    try:
        existing_checksums = load_existing_checksums(checksum_file)
    except Exception as e:
        logger.error(f"Failed to load existing checksums: {e}")
        return 1

    # Update checksums with relative path from data directory
    relative_path = str(target_file.relative_to(data_dir))
    existing_checksums[relative_path] = {
        "sha256": checksum,
        "file": str(target_file.name)
    }

    # Save updated checksums
    try:
        save_checksums(existing_checksums, checksum_file)
        logger.info(f"Updated checksums saved to {checksum_file}")
    except Exception as e:
        logger.error(f"Failed to save checksums: {e}")
        return 1

    logger.info("Task T052 completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())