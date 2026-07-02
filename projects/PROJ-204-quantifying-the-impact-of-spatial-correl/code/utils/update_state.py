"""
Module to update the project state file with checksums of data artifacts.

This script scans the `data/` directory for all files, computes their SHA-256
checksums, and updates the project state YAML file located at:
`state/projects/PROJ-204-quantifying-the-impact-of-spatial-correl.yaml`
with an `artifact_hashes` map.
"""
import os
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, List
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ID = "PROJ-204-quantifying-the-impact-of-spatial-correl"
DATA_DIR = Path("data")
STATE_DIR = Path("state") / "projects"
STATE_FILE = STATE_DIR / f"{PROJECT_ID}.yaml"


def compute_file_hash(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to hash file {file_path}: {e}")
        raise


def scan_data_directory(data_root: Path) -> Dict[str, str]:
    """
    Recursively scan the data directory and compute hashes for all files.

    Args:
        data_root: Root path of the data directory.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    if not data_root.exists():
        logger.warning(f"Data directory {data_root} does not exist. Returning empty map.")
        return {}

    artifact_hashes = {}
    for file_path in data_root.rglob("*"):
        if file_path.is_file():
            relative_path = str(file_path.relative_to(data_root))
            try:
                file_hash = compute_file_hash(file_path)
                artifact_hashes[relative_path] = file_hash
                logger.debug(f"Hashed: {relative_path} -> {file_hash[:16]}...")
            except Exception:
                logger.warning(f"Skipping unhashable file: {relative_path}")
                continue

    return artifact_hashes


def load_or_create_state(project_id: str, state_file: Path) -> Dict[str, Any]:
    """
    Load existing state file or create a new one with default structure.

    Args:
        project_id: The project identifier.
        state_file: Path to the state YAML file.

    Returns:
        The state dictionary.
    """
    if state_file.exists():
        logger.info(f"Loading existing state from {state_file}")
        with open(state_file, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f) or {}
    else:
        logger.info(f"State file {state_file} not found. Creating new state.")
        state = {
            "project_id": project_id,
            "status": "initialized",
            "artifact_hashes": {}
        }

    # Ensure project_id matches
    if state.get("project_id") != project_id:
        logger.warning(f"State file project_id mismatch. Expected {project_id}, got {state.get('project_id')}. Overwriting project_id.")
        state["project_id"] = project_id

    return state


def update_state_file(state: Dict[str, Any], artifact_hashes: Dict[str, str], state_file: Path) -> None:
    """
    Update the state dictionary with new artifact hashes and write to disk.

    Args:
        state: The state dictionary to update.
        artifact_hashes: The new map of file paths to hashes.
        state_file: Path to the output YAML file.
    """
    state["artifact_hashes"] = artifact_hashes
    state["last_updated"] = "auto-generated" # Placeholder for timestamp if needed

    # Ensure directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing updated state to {state_file}")
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)


def update_state() -> None:
    """
    Main entry point to scan data and update the project state file.
    """
    logger.info(f"Starting state update for project: {PROJECT_ID}")

    # Ensure data directory exists before scanning
    if not DATA_DIR.exists():
        logger.error(f"Data directory {DATA_DIR} does not exist. Cannot compute checksums.")
        raise FileNotFoundError(f"Data directory not found: {DATA_DIR}")

    # Scan data directory
    logger.info(f"Scanning {DATA_DIR} for artifacts...")
    artifact_hashes = scan_data_directory(DATA_DIR)
    logger.info(f"Found {len(artifact_hashes)} artifacts.")

    # Load or create state
    state = load_or_create_state(PROJECT_ID, STATE_FILE)

    # Update state
    update_state_file(state, artifact_hashes, STATE_FILE)

    logger.info("State update completed successfully.")


if __name__ == "__main__":
    update_state()
