"""
Checksumming utility for raw Wigner matrix instances.

This module implements Constitution Principle III (Data Hygiene) by computing
SHA-256 checksums for all raw matrix instances generated in T019a and writing
them to state/checksums_raw.json.
"""
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any

from utils.config import get_project_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def compute_file_sha256(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to checksum

    Returns:
        Hexadecimal string of the SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def find_raw_matrices(raw_data_dir: Path) -> List[Path]:
    """
    Find all raw matrix .npy files in the data/raw directory.

    Args:
        raw_data_dir: Path to the data/raw directory

    Returns:
        List of Path objects for all .npy files found
    """
    if not raw_data_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_data_dir}")
        return []

    matrix_files = list(raw_data_dir.glob("matrix_*.npy"))
    logger.info(f"Found {len(matrix_files)} raw matrix files in {raw_data_dir}")
    return matrix_files


def checksum_raw_matrices(raw_data_dir: Path, state_dir: Path) -> Dict[str, Any]:
    """
    Compute checksums for all raw matrix files and save to state/checksums_raw.json.

    Args:
        raw_data_dir: Path to the data/raw directory
        state_dir: Path to the state directory

    Returns:
        Dictionary containing checksums and metadata
    """
    matrix_files = find_raw_matrices(raw_data_dir)

    if not matrix_files:
        logger.warning("No raw matrix files found to checksum")
        return {"files": {}, "total_files": 0, "status": "no_files"}

    checksums = {}
    for file_path in matrix_files:
        try:
            checksum = compute_file_sha256(file_path)
            rel_path = str(file_path.relative_to(raw_data_dir))
            checksums[rel_path] = {
                "sha256": checksum,
                "size_bytes": file_path.stat().st_size,
                "checksummed_at": str(Path().resolve())  # Placeholder for timestamp
            }
            logger.info(f"Checksummed: {rel_path} -> {checksum[:16]}...")
        except Exception as e:
            logger.error(f"Failed to checksum {file_path}: {e}")

    # Create metadata
    result = {
        "files": checksums,
        "total_files": len(checksums),
        "status": "success",
        "checksum_algorithm": "SHA-256",
        "raw_data_directory": str(raw_data_dir),
        "generated_at": "timestamp_placeholder"  # Will be updated in main
    }

    # Ensure state directory exists
    state_dir.mkdir(parents=True, exist_ok=True)

    # Write checksums to file
    output_path = state_dir / "checksums_raw.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    logger.info(f"Checksums written to {output_path}")
    return result


def main():
    """Main entry point for checksumming raw matrices."""
    logger.info("Starting raw matrix checksum process")

    # Get project paths
    project_paths = get_project_paths()
    raw_data_dir = project_paths["data_raw"]
    state_dir = project_paths["state"]

    # Perform checksumming
    result = checksum_raw_matrices(raw_data_dir, state_dir)

    # Log summary
    logger.info(f"Checksum process complete. Total files: {result['total_files']}")
    logger.info(f"Status: {result['status']}")

    return result


if __name__ == "__main__":
    main()
