"""
Data hygiene utilities: Checksums and Metadata Registry management.
Implements Constitution Principle III (Data Hygiene).
"""

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

def compute_file_sha256(filepath: Path) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        filepath: Path to the file.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Read in chunks for large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_existing_checksums(metadata_file: Path) -> Dict[str, Any]:
    """
    Load the existing metadata registry, or return a default structure if it doesn't exist.

    Args:
        metadata_file: Path to the metadata JSON file.

    Returns:
        Dictionary with 'runs' key containing a list of run metadata.
    """
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            return json.load(f)
    else:
        logger.info(f"Metadata file {metadata_file} not found. Creating new registry.")
        return {"runs": []}

def save_checksums(metadata_file: Path, data: Dict[str, Any]) -> None:
    """
    Save the metadata registry to disk.

    Args:
        metadata_file: Path to the metadata JSON file.
        data: Dictionary to save.
    """
    with open(metadata_file, 'w') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved metadata registry to {metadata_file}")

def update_metadata_registry(
    metadata_file: Path,
    new_entries: List[Dict[str, Any]]
) -> None:
    """
    Atomically update the metadata registry with new entries.
    Appends new entries to the existing 'runs' list.

    Args:
        metadata_file: Path to the metadata JSON file.
        new_entries: List of new run metadata dictionaries.
    """
    registry = load_existing_checksums(metadata_file)

    # Check for duplicates to avoid overwriting
    existing_ids = {run["run_id"] for run in registry["runs"]}
    for entry in new_entries:
        if entry["run_id"] in existing_ids:
            logger.warning(f"Run ID {entry['run_id']} already exists. Skipping update.")
        else:
            registry["runs"].append(entry)
            existing_ids.add(entry["run_id"])

    save_checksums(metadata_file, registry)

def find_raw_matrices(raw_data_dir: Path) -> List[Path]:
    """
    Find all .npy files in the raw data directory.

    Args:
        raw_data_dir: Path to the raw data directory.

    Returns:
        List of Path objects for .npy files.
    """
    if not raw_data_dir.exists():
        return []
    return list(raw_data_dir.glob("*.npy"))

def checksum_raw_matrices(raw_data_dir: Path, metadata_file: Path) -> None:
    """
    Compute checksums for all .npy files in the raw data directory and update the registry.

    Args:
        raw_data_dir: Path to the raw data directory.
        metadata_file: Path to the metadata JSON file.
    """
    matrix_files = find_raw_matrices(raw_data_dir)
    if not matrix_files:
        logger.warning(f"No .npy files found in {raw_data_dir}")
        return

    new_entries = []
    for filepath in matrix_files:
        checksum = compute_file_sha256(filepath)
        entry = {
            "run_id": filepath.stem,
            "checksum": checksum,
            "parameters": {}, # Parameters should be filled by the generator
            "file_path": str(filepath)
        }
        new_entries.append(entry)
        logger.info(f"Checksummed {filepath.name}: {checksum}")

    update_metadata_registry(metadata_file, new_entries)