"""
Artifact Versioning Module for PROJ-224.

This module handles the computation of SHA-256 hashes for data artifacts
and manages the central state file where these hashes are recorded.
"""
import hashlib
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Project root relative to this file (code/data/ -> root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-224-predicting-the-ductility-of-additively-m.yaml"
CURATED_DATA_PATH = PROJECT_ROOT / "data" / "curated_builds.csv"

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
        raise FileNotFoundError(f"File not found for hashing: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}") from e


def ensure_state_file() -> Path:
    """
    Ensure the state directory and file exist.

    Returns:
        Path to the state YAML file.
    """
    state_dir = STATE_FILE_PATH.parent
    state_dir.mkdir(parents=True, exist_ok=True)

    if not STATE_FILE_PATH.exists():
        logger.info(f"Creating new state file at {STATE_FILE_PATH}")
        # Initialize with empty structure
        with open(STATE_FILE_PATH, "w", encoding="utf-8") as f:
            f.write("project_id: PROJ-224-predicting-the-ductility-of-additively-m\n")
            f.write("artifact_hashes: {}\n")
    else:
        logger.debug(f"State file already exists at {STATE_FILE_PATH}")

    return STATE_FILE_PATH


def save_state(hashes: dict) -> None:
    """
    Save the artifact hashes to the state YAML file.

    Args:
        hashes: Dictionary mapping artifact names to their SHA-256 hashes.
    """
    import yaml

    # Ensure state file exists
    ensure_state_file()

    # Read existing content
    with open(STATE_FILE_PATH, "r", encoding="utf-8") as f:
        try:
            state_data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logger.warning(f"Could not parse existing state file: {e}. Overwriting.")
            state_data = {}

    # Update artifact_hashes
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}

    state_data["artifact_hashes"].update(hashes)

    # Write back
    with open(STATE_FILE_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump(state_data, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Updated state file at {STATE_FILE_PATH}")


def version_artifact(artifact_path: Path, artifact_name: Optional[str] = None) -> str:
    """
    Compute the hash of an artifact and record it in the state file.

    Args:
        artifact_path: Path to the artifact file.
        artifact_name: Optional name for the artifact. Defaults to the file stem.

    Returns:
        The computed SHA-256 hash.

    Raises:
        FileNotFoundError: If the artifact file does not exist.
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found for versioning: {artifact_path}")

    if artifact_name is None:
        artifact_name = artifact_path.stem

    logger.info(f"Versioning artifact: {artifact_name} -> {artifact_path}")

    # Compute hash
    file_hash = compute_sha256(artifact_path)
    logger.info(f"Computed SHA-256 for {artifact_name}: {file_hash}")

    # Save to state
    save_state({artifact_name: file_hash})

    return file_hash


def main() -> int:
    """
    Main entry point for versioning the curated dataset.

    Returns:
        0 on success, 1 on failure.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    try:
        if not CURATED_DATA_PATH.exists():
            logger.error(f"Curated data file not found at {CURATED_DATA_PATH}")
            logger.error("Please ensure T017 (data cleaning) has been run successfully.")
            return 1

        hash_value = version_artifact(CURATED_DATA_PATH, "curated_builds_csv")
        logger.info(f"SUCCESS: Artifact versioned. Hash: {hash_value}")
        logger.info(f"State file updated at: {STATE_FILE_PATH}")
        return 0

    except Exception as e:
        logger.error(f"Failed to version artifact: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
