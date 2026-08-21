"""
Hashing utilities for artifact integrity verification.
Implements SHA-256 checksumming for simulation-derived CSVs and updates state/artifact_hashes.yaml.
"""

import hashlib
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import from existing project modules
from code.config import get_path
from code.utils.logging import get_logger, log_pipeline_step

# Configure logger
logger = get_logger(__name__)

# Constants
STATE_FILE = "state/artifact_hashes.yaml"
SIMULATION_DATA_FILES = [
    "data/raw/synthetic_mfq.csv",
    "data/raw/synthetic_stories.csv",
    "data/raw/synthetic_vr_logs.csv",
    "data/processed/merged_data.csv",
    "data/processed/preprocessed_data.csv"
]


def calculate_sha256(file_path: str) -> str:
    """
    Calculate SHA-256 checksum for a given file.

    Args:
        file_path: Path to the file to checksum.

    Returns:
        Hex digest of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file {file_path}: {e}")


def update_state_yaml(hashes: Dict[str, str]) -> None:
    """
    Update the state/artifact_hashes.yaml file with new checksums.

    Args:
        hashes: Dictionary mapping file paths (relative to project root) to their SHA-256 hashes.
    """
    state_path = Path(get_path(STATE_FILE))
    state_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing state if it exists
    existing_hashes = {}
    if state_path.exists():
        try:
            with open(state_path, "r") as f:
                existing_data = json.load(f)
                existing_hashes = existing_data.get("artifact_hashes", {})
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not parse existing state file: {e}. Starting fresh.")

    # Merge new hashes
    existing_hashes.update(hashes)

    # Write updated state
    state_data = {
        "artifact_hashes": existing_hashes,
        "updated_at": str(Path().cwd())  # Simple timestamp placeholder
    }

    with open(state_path, "w") as f:
        json.dump(state_data, f, indent=2)

    log_pipeline_step("hashing", f"Updated {len(hashes)} checksums in {STATE_FILE}")
    logger.info(f"Checksums written to {state_path}")


def verify_artifact(file_path: str, expected_hash: str) -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_hash: Expected SHA-256 hex digest.

    Returns:
        True if the hash matches, False otherwise.
    """
    try:
        actual_hash = calculate_sha256(file_path)
        return actual_hash == expected_hash
    except (FileNotFoundError, IOError) as e:
        logger.error(f"Verification failed for {file_path}: {e}")
        return False


def checksum_derived_datasets() -> Dict[str, str]:
    """
    Calculate checksums for all simulation-derived CSVs and return the mapping.

    Returns:
        Dictionary mapping file paths to their SHA-256 hashes.
    """
    results = {}
    for file_rel_path in SIMULATION_DATA_FILES:
        full_path = get_path(file_rel_path)
        if os.path.exists(full_path):
            try:
                hash_val = calculate_sha256(full_path)
                results[file_rel_path] = hash_val
                logger.info(f"Checksummed {file_rel_path}: {hash_val[:16]}...")
            except IOError as e:
                logger.error(f"Failed to checksum {file_rel_path}: {e}")
        else:
            logger.warning(f"Skipping missing file: {file_rel_path}")
    return results


def update_state_checksums() -> None:
    """
    Main entry point: checksum all derived datasets and update the state file.
    """
    log_pipeline_step("hashing", "Starting artifact checksumming for simulation-derived data")
    hashes = checksum_derived_datasets()
    if hashes:
        update_state_yaml(hashes)
    else:
        logger.warning("No checksums calculated. No derived data files found.")


def main() -> None:
    """
    CLI entry point for T018.
    Checks simulation-derived CSVs and updates state/artifact_hashes.yaml.
    """
    logger.info("Running T018: Hashing simulation-derived artifacts")
    update_state_checksums()
    logger.info("T018 completed successfully")


if __name__ == "__main__":
    main()