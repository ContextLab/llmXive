"""
Artifact versioning module for PROJ-224.
Computes SHA-256 hashes and updates the project state file.
"""
import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise


def ensure_state_file(state_path: Path) -> Dict[str, Any]:
    """
    Ensure the state file exists and return its contents.
    Creates the file with default structure if it doesn't exist.

    Args:
        state_path: Path to the state YAML file.

    Returns:
        Dictionary containing the state file contents.
    """
    # Ensure parent directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    if not state_path.exists():
        logger.info(f"Creating new state file at {state_path}")
        state_data = {
            "artifact_hashes": {}
        }
        with open(state_path, 'w', encoding='utf-8') as f:
            yaml.dump(state_data, f, default_flow_style=False)
        return state_data

    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            state_data = yaml.safe_load(f)
            if state_data is None:
                state_data = {"artifact_hashes": {}}
            if "artifact_hashes" not in state_data:
                state_data["artifact_hashes"] = {}
        return state_data
    except yaml.YAMLError as e:
        logger.error(f"Error parsing existing state file {state_path}: {e}")
        raise


def save_state(state_path: Path, state_data: Dict[str, Any]) -> None:
    """
    Save the state dictionary to the YAML file.

    Args:
        state_path: Path to the state YAML file.
        state_data: Dictionary to save.
    """
    try:
        with open(state_path, 'w', encoding='utf-8') as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State saved to {state_path}")
    except IOError as e:
        logger.error(f"Error writing state file {state_path}: {e}")
        raise


def version_artifact(
    artifact_path: Path,
    state_path: Path,
    key_name: Optional[str] = None
) -> str:
    """
    Version an artifact by computing its hash and recording it in the state file.

    Args:
        artifact_path: Path to the artifact file to version.
        state_path: Path to the project state YAML file.
        key_name: Optional custom key name for the artifact in the state file.
                 If None, uses the relative path from project root.

    Returns:
        The computed SHA-256 hash.

    Raises:
        FileNotFoundError: If the artifact does not exist.
        ValueError: If the hash verification fails after writing.
    """
    if not artifact_path.is_absolute():
        # Assume relative to current working directory (project root)
        artifact_path = Path.cwd() / artifact_path

    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found for versioning: {artifact_path}")

    # Compute hash
    file_hash = compute_sha256(artifact_path)
    logger.info(f"Computed SHA-256 for {artifact_path}: {file_hash}")

    # Determine key name
    if key_name is None:
        # Use relative path from current working directory
        try:
            key_name = str(artifact_path.relative_to(Path.cwd()))
        except ValueError:
            key_name = str(artifact_path)

    # Load or create state
    state_data = ensure_state_file(state_path)

    # Update hash
    old_hash = state_data["artifact_hashes"].get(key_name)
    state_data["artifact_hashes"][key_name] = file_hash
    save_state(state_path, state_data)

    # Verify
    if state_data["artifact_hashes"][key_name] != file_hash:
        raise ValueError(
            f"Hash verification failed for {key_name}. "
            f"Expected: {file_hash}, Found: {state_data['artifact_hashes'][key_name]}"
        )

    logger.info(f"Artifact versioned successfully: {key_name} -> {file_hash}")
    return file_hash


def main() -> int:
    """
    Main entry point for artifact versioning.
    Versions data/curated_builds_features.csv and updates state/projects/PROJ-224.yaml.
    """
    project_root = Path.cwd()
    artifact_file = project_root / "data" / "curated_builds_features.csv"
    state_file = (
        project_root / "state" / "projects" /
        "PROJ-224-predicting-the-ductility-of-additively-m.yaml"
    )

    logger.info(f"Starting artifact versioning for {artifact_file}")

    try:
        # Version the artifact
        hash_value = version_artifact(artifact_file, state_file)

        logger.info(f"SUCCESS: Artifact versioned. Hash: {hash_value}")
        return 0

    except FileNotFoundError as e:
        logger.critical(f"Failed to version artifact: {e}")
        return 1
    except ValueError as e:
        logger.critical(f"Versioning verification failed: {e}")
        return 1
    except Exception as e:
        logger.critical(f"Unexpected error during versioning: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
