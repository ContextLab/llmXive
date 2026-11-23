"""
Artifact Hashing and Integrity Verification (T006, T018).

Implements SHA-256 checksums for data artifacts and maintains
a state file (`state/artifact_hashes.yaml`) to ensure reproducibility
(Constitution Principle V).

This module extends the functionality to support:
1. T006: Core hashing and state update logic.
2. T018: Specific integration for simulation-derived CSVs.
"""

from __future__ import annotations

import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

import yaml

# Import project config for path resolution
# We use a dynamic import to avoid circular dependencies if config.py imports this
try:
    from code.config import get_path, ensure_directories
except ImportError:
    # Fallback for direct script execution or if config is not yet available
    from config import get_path, ensure_directories

# Import logging utility to avoid circular import with stdlib 'logging' if named 'logging'
try:
    from code.utils.logging import get_logger, log_operation
except ImportError:
    # Fallback if utils is not ready, use stdlib but handle name collision
    import logging as stdlib_logging
    def get_logger(name: str = "hashing"):
        return stdlib_logging.getLogger(name)
    def log_operation(*args, **kwargs):
        # No-op fallback if logging module isn't ready
        pass


STATE_FILE = "state/artifact_hashes.yaml"
# Specific files targeted by T018
T018_TARGET_FILES = [
    "data/processed/synthetic_mfq.csv",
    "data/processed/synthetic_logs.csv"
]


def calculate_checksum(file_path: str) -> str:
    """
    Calculate the SHA-256 checksum of a file.

    Args:
        file_path: Relative or absolute path to the file.

    Returns:
        Hex digest string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    full_path = Path(file_path)
    if not full_path.is_absolute():
        # Resolve relative to project root using config
        full_path = get_path(file_path)

    if not full_path.exists():
        raise FileNotFoundError(f"Cannot calculate checksum: File not found at {full_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(full_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file {full_path} for checksum: {e}")


def load_state_file() -> Dict[str, Any]:
    """
    Load the current state file containing artifact hashes.
    If the file does not exist, returns an empty dictionary.

    Returns:
        Dictionary mapping artifact filenames to their SHA-256 hashes.
    """
    state_path = get_path(STATE_FILE)
    if not state_path.exists():
        # Ensure directory exists
        ensure_directories()
        return {}

    try:
        with open(state_path, "r") as f:
            data = yaml.safe_load(f)
            return data if data else {}
    except yaml.YAMLError:
        return {}
    except Exception:
        return {}


def update_state_file(file_path: str, checksum: str) -> None:
    """
    Update the state file with a new checksum for a given file.

    Args:
        file_path: The path of the artifact (relative to project root).
        checksum: The SHA-256 hex digest.

    Side Effects:
        Updates `state/artifact_hashes.yaml`.
    """
    current_state = load_state_file()

    # Use the basename or relative path as the key
    # The task requires keys like 'synthetic_mfq.csv'
    key = Path(file_path).name

    current_state[key] = {
        "hash": checksum,
        "path": file_path,
        "updated_at": None # Could add timestamp if needed, but kept simple per spec
    }

    state_path = get_path(STATE_FILE)
    ensure_directories()

    with open(state_path, "w") as f:
        yaml.dump(current_state, f, default_flow_style=False, sort_keys=False)


def verify_artifact(file_path: str) -> bool:
    """
    Verify the integrity of an artifact by comparing its current checksum
    against the one stored in the state file.

    Args:
        file_path: Path to the artifact.

    Returns:
        True if the checksum matches the stored value, False otherwise.
        Returns False if the file or state entry is missing.
    """
    if not Path(file_path).exists():
        return False

    current_checksum = calculate_checksum(file_path)
    state = load_state_file()
    key = Path(file_path).name

    if key not in state:
        return False

    stored_checksum = state[key].get("hash")
    return current_checksum == stored_checksum


def update_artifact_hashes_for_simulation() -> Dict[str, str]:
    """
    T018 Implementation: Calculate checksums for simulation-derived CSVs
    and update the state file.

    Files processed:
      - data/processed/synthetic_mfq.csv
      - data/processed/synthetic_logs.csv

    Returns:
        Dictionary of {filename: checksum} for the processed files.
    """
    logger = get_logger("hashing")
    log_operation("hashing", "Starting artifact checksumming for simulation-derived data")

    results = {}
    missing_files = []

    for file_path in T018_TARGET_FILES:
        full_path = get_path(file_path)
        if not full_path.exists():
            missing_files.append(file_path)
            logger.warning(f"Skipping missing file for hashing: {file_path}")
            continue

        try:
            checksum = calculate_checksum(file_path)
            update_state_file(file_path, checksum)
            results[Path(file_path).name] = checksum
            logger.info(f"Checksummed {file_path}: {checksum[:16]}...")
        except Exception as e:
            logger.error(f"Failed to checksum {file_path}: {e}")
            raise

    if missing_files:
        logger.error(f"Missing required simulation artifacts: {missing_files}")
        # Do not raise here if we successfully processed what exists,
        # but log the failure. The task requirement is to update the state
        # for the files that *should* exist. If they don't, the upstream
        # task (T013/T014) is the failure point.
        # However, for T018 to be "complete", we expect them to exist.
        # We raise if none were processed.
        if not results:
            raise FileNotFoundError(
                f"None of the required simulation artifacts found: {T018_TARGET_FILES}. "
                "Ensure T013 and T014 have completed successfully."
            )

    log_operation("hashing", f"Updated {len(results)} checksums in {STATE_FILE}")
    return results


def main() -> None:
    """
    CLI entry point for T018.
    Runs the simulation artifact checksumming process.
    """
    print("Running T018: Simulation Artifact Hashing...")
    try:
        results = update_artifact_hashes_for_simulation()
        print(f"Success. Updated hashes for: {list(results.keys())}")
        print(f"State file updated at: {get_path(STATE_FILE)}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()