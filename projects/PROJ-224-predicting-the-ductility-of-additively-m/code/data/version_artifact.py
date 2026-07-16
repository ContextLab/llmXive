"""
Artifact Versioning Module for PROJ-224.

This module handles the computation of SHA-256 hashes for data artifacts
and the management of the project state file to record these hashes.
"""

import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root is assumed to be the parent of the 'code' directory
# We traverse up from the current file location
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE_PATH = STATE_DIR / "PROJ-224-predicting-the-ductility-of-additively-m.yaml"

def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path (Path): Path to the file to hash.

    Returns:
        str: The hexadecimal SHA-256 hash string.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

def ensure_state_file() -> Dict[str, Any]:
    """
    Ensures the state file exists and returns its current content.
    Creates the file with the required structure if it does not exist.

    Returns:
        Dict[str, Any]: The current content of the state file.
    """
    # Ensure the directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    state_data = {}

    if STATE_FILE_PATH.exists():
        try:
            import yaml
            with open(STATE_FILE_PATH, 'r') as f:
                state_data = yaml.safe_load(f) or {}
            logger.info(f"Loaded existing state file: {STATE_FILE_PATH}")
        except Exception as e:
            logger.warning(f"Could not read existing state file {STATE_FILE_PATH}: {e}. Starting fresh.")
            state_data = {}
    else:
        logger.info(f"State file {STATE_FILE_PATH} does not exist. Creating new structure.")

    # Ensure the 'artifact_hashes' key exists
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}

    return state_data

def save_state(state_data: Dict[str, Any]) -> None:
    """
    Saves the state dictionary to the YAML file.

    Args:
        state_data (Dict[str, Any]): The data to save.
    """
    try:
        import yaml
        with open(STATE_FILE_PATH, 'w') as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State saved to {STATE_FILE_PATH}")
    except Exception as e:
        logger.error(f"Failed to save state file {STATE_FILE_PATH}: {e}")
        raise

def version_artifact(artifact_path: Path, state_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Computes the hash of an artifact, updates the state data, and saves it.

    Args:
        artifact_path (Path): Path to the artifact file.
        state_data (Optional[Dict[str, Any]]): Existing state data. If None, loads from file.

    Returns:
        str: The computed hash.

    Raises:
        FileNotFoundError: If the artifact file does not exist.
        ValueError: If the state data structure is invalid.
    """
    if state_data is None:
        state_data = ensure_state_file()

    # Compute hash
    hash_value = compute_sha256(artifact_path)
    logger.info(f"Computed SHA-256 for {artifact_path.name}: {hash_value}")

    # Update state
    artifact_key = str(artifact_path.relative_to(PROJECT_ROOT))
    state_data["artifact_hashes"][artifact_key] = hash_value

    # Save state
    save_state(state_data)

    # Verification
    if state_data["artifact_hashes"].get(artifact_key) != hash_value:
        raise ValueError(f"Verification failed: Hash mismatch for {artifact_key}")

    logger.info(f"Successfully versioned artifact: {artifact_key}")
    return hash_value

def main():
    """
    Main entry point for versioning the specific US1 artifact.
    """
    # Define the target artifact relative to project root
    # The task specifies: data/curated_builds_features.csv
    target_artifact = PROJECT_ROOT / "data" / "curated_builds_features.csv"

    logger.info(f"Starting artifact versioning for: {target_artifact}")

    if not target_artifact.exists():
        logger.error(f"CRITICAL: Target artifact does not exist: {target_artifact}")
        logger.error("The pipeline up to T018 (preprocessing) has not produced the required file.")
        logger.error("Please ensure code/data/preprocessing.py has been run successfully.")
        sys.exit(1)

    try:
        hash_value = version_artifact(target_artifact)
        print(f"SUCCESS: Artifact {target_artifact} versioned.")
        print(f"Hash: {hash_value}")
        print(f"State file updated: {STATE_FILE_PATH}")
    except Exception as e:
        logger.error(f"Failed to version artifact: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
