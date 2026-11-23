"""
Checksum Recording Module for llmXive Project PROJ-268.

This module handles the recording of SHA256 checksums for downloaded and
processed data artifacts into the project state YAML file.

Dependencies:
    - utils: compute_sha256, verify_sha256
    - logging_config: get_logger
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from utils import compute_sha256
from logging_config import get_logger

logger = get_logger()

# Project root relative to code/
PROJECT_ROOT = Path(__file__).parent.parent
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-268-the-impact-of-network-centrality-on-neur.yaml"


def ensure_state_file_exists() -> Path:
    """
    Ensures the state YAML file and its parent directory exist.
    Initializes the file with a basic structure if it doesn't exist.
    """
    STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not STATE_FILE_PATH.exists():
        logger.info(f"State file {STATE_FILE_PATH} not found. Initializing...")
        initial_data = {
            "project_id": "PROJ-268-the-impact-of-network-centrality-on-neur",
            "last_updated": None,
            "artifacts": {}
        }
        with open(STATE_FILE_PATH, 'w') as f:
            yaml.dump(initial_data, f, default_flow_style=False)
        logger.info(f"Initialized state file at {STATE_FILE_PATH}")
    else:
        logger.debug(f"State file {STATE_FILE_PATH} already exists.")

    return STATE_FILE_PATH


def load_state() -> Dict[str, Any]:
    """
    Loads the current state from the YAML file.
    """
    state_path = ensure_state_file_exists()
    with open(state_path, 'r') as f:
        return yaml.safe_load(f)


def save_state(state: Dict[str, Any]) -> None:
    """
    Saves the state dictionary back to the YAML file.
    """
    state_path = ensure_state_file_exists()
    state["last_updated"] = datetime.now().isoformat()
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
    logger.info(f"State saved to {state_path}")


def record_checksums(
    file_paths: List[str],
    artifact_type: str,
    description: str = ""
) -> Dict[str, str]:
    """
    Computes SHA256 checksums for a list of file paths and records them
    in the state YAML file.

    Args:
        file_paths: List of absolute or relative paths to files.
        artifact_type: A category label for the artifacts (e.g., 'raw_nifti', 'processed_matrix').
        description: Optional description of the batch of artifacts.

    Returns:
        A dictionary of relative_path -> checksum.
    """
    state = load_state()
    if "artifacts" not in state:
        state["artifacts"] = {}

    if artifact_type not in state["artifacts"]:
        state["artifacts"][artifact_type] = {
            "description": description,
            "entries": {}
        }

    recorded = {}

    for file_path in file_paths:
        path_obj = Path(file_path)
        
        # Resolve to absolute to ensure consistency, then store relative to root
        if path_obj.is_absolute():
            try:
                rel_path = path_obj.relative_to(PROJECT_ROOT)
            except ValueError:
                # If not under project root, use absolute path
                rel_path = path_obj
        else:
            rel_path = path_obj

        full_path = PROJECT_ROOT / rel_path

        if not full_path.exists():
            logger.warning(f"File not found, skipping checksum: {full_path}")
            continue

        try:
            checksum = compute_sha256(str(full_path))
            recorded[str(rel_path)] = checksum
            state["artifacts"][artifact_type]["entries"][str(rel_path)] = {
                "checksum": checksum,
                "timestamp": datetime.now().isoformat()
            }
            logger.info(f"Recorded checksum for {rel_path}: {checksum[:16]}...")
        except Exception as e:
            logger.error(f"Failed to compute checksum for {full_path}: {e}")
            raise

    save_state(state)
    return recorded


def verify_checksums(artifact_type: str) -> bool:
    """
    Verifies all checksums recorded for a specific artifact type against
    the actual files on disk.

    Args:
        artifact_type: The category label in the state file.

    Returns:
        True if all checksums match, False otherwise.
    """
    state = load_state()
    if "artifacts" not in state or artifact_type not in state["artifacts"]:
        logger.warning(f"No artifacts found for type '{artifact_type}' in state.")
        return False

    entries = state["artifacts"][artifact_type]["entries"]
    all_valid = True

    for rel_path_str, data in entries.items():
        expected_checksum = data["checksum"]
        path_obj = Path(rel_path_str)
        full_path = PROJECT_ROOT / path_obj

        if not full_path.exists():
            logger.error(f"File missing for verification: {full_path}")
            all_valid = False
            continue

        try:
            actual_checksum = compute_sha256(str(full_path))
            if actual_checksum != expected_checksum:
                logger.error(f"Checksum mismatch for {full_path}")
                logger.error(f"  Expected: {expected_checksum}")
                logger.error(f"  Actual:   {actual_checksum}")
                all_valid = False
            else:
                logger.debug(f"Checksum verified for {full_path}")
        except Exception as e:
            logger.error(f"Error verifying {full_path}: {e}")
            all_valid = False

    return all_valid


def main():
    """
    Entry point for manual checksum recording.
    Example usage: python code/checksums.py data/processed/subject_001_SC.npy
    """
    import sys

    if len(sys.argv) < 2:
        print("Usage: python code/checksums.py <file_path> [file_path2 ...] [artifact_type]")
        print("Default artifact_type is 'manual_batch'")
        sys.exit(1)

    files = sys.argv[1:-1] if len(sys.argv) > 2 else sys.argv[1:]
    artifact_type = sys.argv[-1] if len(sys.argv) > 2 else "manual_batch"

    logger.info(f"Recording checksums for {len(files)} files under type '{artifact_type}'...")
    try:
        record_checksums(files, artifact_type)
        print("Checksums recorded successfully.")
    except Exception as e:
        print(f"Error recording checksums: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
