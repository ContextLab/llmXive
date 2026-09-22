"""
Artifact versioning utility for llmXive research pipeline.

This module manages the state of the project by computing cryptographic hashes
of all files in the data directory and updating the project state YAML file.
"""
import os
import yaml
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from config import Paths, get_project_id
from utils.logger import get_logger

logger = get_logger(__name__)


def get_state_file_path() -> Path:
    """
    Get the path to the project state YAML file.

    Returns:
        Path: Absolute path to the state file.
    """
    project_id = get_project_id()
    state_dir = Paths.STATE_DIR / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / f"{project_id}.yaml"


def load_state_file() -> Dict[str, Any]:
    """
    Load the current state file or create a new one if it doesn't exist.

    Returns:
        Dict[str, Any]: The state dictionary.
    """
    state_path = get_state_file_path()
    if state_path.exists():
        with open(state_path, 'r', encoding='utf-8') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {
            "project_id": get_project_id(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": None,
            "artifact_hashes": {},
            "metadata": {}
        }
    return state


def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        str: Hexadecimal SHA-256 hash string.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def compute_artifact_checksums(data_dir: Optional[Path] = None) -> Dict[str, str]:
    """
    Compute cryptographic hashes for all files in the data directory.

    Args:
        data_dir: Optional path to data directory. Defaults to Paths.DATA_DIR.

    Returns:
        Dict[str, str]: Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    if data_dir is None:
        data_dir = Paths.DATA_DIR

    if not data_dir.exists():
        logger.warning(f"Data directory does not exist: {data_dir}")
        return {}

    hashes = {}
    for root, _, files in os.walk(data_dir):
        for file in files:
            file_path = Path(root) / file
            relative_path = file_path.relative_to(Paths.PROJECT_ROOT)
            try:
                file_hash = compute_sha256(file_path)
                hashes[str(relative_path)] = file_hash
                logger.debug(f"Hashed {relative_path}: {file_hash[:16]}...")
            except Exception as e:
                logger.error(f"Failed to hash {relative_path}: {e}")

    return hashes


def update_state_file(state: Dict[str, Any], new_hashes: Dict[str, str]) -> Path:
    """
    Update the state file with new artifact hashes and timestamp.

    Args:
        state: Current state dictionary.
        new_hashes: New artifact hashes to write.

    Returns:
        Path: Path to the updated state file.
    """
    state_path = get_state_file_path()
    state["artifact_hashes"] = new_hashes
    state["updated_at"] = datetime.utcnow().isoformat()

    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Updated state file at {state_path}")
    return state_path


def record_data_generation_state() -> Dict[str, Any]:
    """
    Main entry point to compute hashes and update the state file after data generation.

    This function:
    1. Loads the current state file (or creates a new one).
    2. Computes SHA-256 hashes for all files in the data directory.
    3. Updates the state file with the new hashes and timestamp.

    Returns:
        Dict[str, Any]: The updated state dictionary.
    """
    logger.info("Starting artifact versioning update...")

    state = load_state_file()
    new_hashes = compute_artifact_checksums()

    if not new_hashes:
        logger.warning("No artifacts found to hash. State file may be updated with empty hashes.")

    update_state_file(state, new_hashes)

    logger.info(f"Versioning complete. Recorded {len(new_hashes)} artifact hashes.")
    return state


def main() -> None:
    """
    CLI entry point for the versioning utility.

    This script can be run directly to update the project state file
    with current artifact hashes.
    """
    try:
        state = record_data_generation_state()
        print(f"State updated successfully. Total artifacts tracked: {len(state.get('artifact_hashes', {}))}")
    except Exception as e:
        logger.error(f"Versioning update failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()