"""
Hashing utilities for artifact integrity and state management.
Implements Constitution Principle V: All derived artifacts must be checksummed.
"""
import hashlib
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

import yaml

from code.config import get_path, ensure_directories

# Configure logger
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: str) -> str:
    """
    Calculate the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file to checksum.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found for checksum: {path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {path} for checksum: {e}")
        raise

def update_state_yaml(
    state_key: str,
    artifact_path: str,
    checksum: str,
    state_file: Optional[str] = None,
) -> None:
    """
    Update the project state YAML file with a new artifact checksum.

    Args:
        state_key: The key under which to store the artifact info (e.g., 'mfq_ingest').
        artifact_path: Relative path to the artifact.
        checksum: The SHA-256 checksum string.
        state_file: Optional path to state file. Defaults to 'state/pipeline_state.yaml'.
    """
    if state_file is None:
        state_file = str(get_path("state", "pipeline_state.yaml"))

    state_path = Path(state_file)
    ensure_directories()

    # Load existing state or initialize
    if state_path.exists():
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                state_data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing state file {state_path}: {e}")
            raise
    else:
        state_data = {}

    # Update the specific key
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}

    state_data["artifact_hashes"][state_key] = {
        "path": str(artifact_path),
        "sha256": checksum,
        "updated_at": None,  # Timestamp can be added by caller if needed
    }

    # Write back
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(state_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Updated state: {state_key} -> {checksum[:16]}...")
    except IOError as e:
        logger.error(f"Failed to write state file {state_path}: {e}")
        raise

def verify_artifact(artifact_path: str, expected_checksum: str) -> bool:
    """
    Verify an artifact's checksum against an expected value.

    Args:
        artifact_path: Path to the artifact.
        expected_checksum: Expected SHA-256 hex string.

    Returns:
        True if checksum matches, False otherwise.
    """
    try:
        actual_checksum = calculate_sha256(artifact_path)
        if actual_checksum == expected_checksum:
            logger.debug(f"Verification passed for {artifact_path}")
            return True
        else:
            logger.warning(
                f"Verification FAILED for {artifact_path}. "
                f"Expected: {expected_checksum}, Got: {actual_checksum}"
            )
            return False
    except FileNotFoundError:
        logger.warning(f"Artifact not found for verification: {artifact_path}")
        return False

def checksum_derived_datasets(
    derived_paths: List[str], state_prefix: str = "derived"
) -> Dict[str, str]:
    """
    Calculate checksums for a list of derived dataset files and update state.

    Args:
        derived_paths: List of relative paths to derived datasets.
        state_prefix: Prefix for state keys (e.g., 'derived_mfq', 'derived_stories').

    Returns:
        Dictionary mapping state keys to checksums.
    """
    results = {}
    for idx, rel_path in enumerate(derived_paths):
        full_path = get_path("", rel_path)
        if not Path(full_path).exists():
            logger.warning(f"Derived dataset not found, skipping checksum: {rel_path}")
            continue

        checksum = calculate_sha256(full_path)
        key = f"{state_prefix}_{idx}"
        update_state_yaml(key, rel_path, checksum)
        results[key] = checksum

    return results

def main() -> None:
    """
    Main entry point for the hashing utility.
    Intended to be called by the pipeline to checksum outputs after generation.
    """
    # This function is typically called programmatically by other pipeline steps.
    # If run directly, it performs a self-check on the state file if it exists.
    state_file = get_path("state", "pipeline_state.yaml")
    if Path(state_file).exists():
        logger.info("State file exists. No specific action required for standalone run.")
        logger.info("Use calculate_sha256() and update_state_yaml() in pipeline steps.")
    else:
        logger.info("No state file found. This utility is designed to be imported.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
