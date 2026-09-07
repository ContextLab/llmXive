import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

from src.utils.io_helpers import setup_logging

logger = setup_logging("state_manager")


def compute_file_hash(file_path: Path) -> Optional[str]:
    """
    Compute SHA-256 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hex digest of the file hash, or None if file does not exist.
    """
    if not file_path.exists():
        logger.warning(f"File not found for hashing: {file_path}")
        return None

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        return None


def scan_directory_for_artifacts(directory: Path) -> Dict[str, str]:
    """
    Scan a directory for files and return a mapping of relative paths to hashes.

    Args:
        directory: Root directory to scan.

    Returns:
        Dictionary mapping relative file paths (str) to their SHA-256 hashes (str).
    """
    artifacts = {}
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return artifacts

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(directory)
            file_hash = compute_file_hash(file_path)
            if file_hash:
                artifacts[str(rel_path)] = file_hash

    return artifacts


def load_state(state_path: Path) -> Dict[str, Any]:
    """
    Load the state YAML file.

    Args:
        state_path: Path to the state YAML file.

    Returns:
        The state dictionary, or an empty dict if the file does not exist.
    """
    if not state_path.exists():
        logger.info(f"State file not found, initializing new state: {state_path}")
        return {
            "project_id": state_path.parent.name,
            "artifact_hashes": {
                "data_raw": {},
                "data_processed": {}
            },
            "last_updated": None
        }

    try:
        with open(state_path, "r") as f:
            state = yaml.safe_load(f)
            if state is None:
                state = {
                    "project_id": state_path.parent.name,
                    "artifact_hashes": {
                        "data_raw": {},
                        "data_processed": {}
                    },
                    "last_updated": None
                }
            return state
    except Exception as e:
        logger.error(f"Error loading state file {state_path}: {e}")
        return {
            "project_id": state_path.parent.name,
            "artifact_hashes": {
                "data_raw": {},
                "data_processed": {}
            },
            "last_updated": None
        }


def save_state(state: Dict[str, Any], state_path: Path) -> None:
    """
    Save the state dictionary to a YAML file.

    Args:
        state: The state dictionary.
        state_path: Path to save the YAML file.
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(state_path, "w") as f:
            yaml.dump(state, f, default_flow_style=False)
        logger.info(f"State saved to {state_path}")
    except Exception as e:
        logger.error(f"Error saving state file {state_path}: {e}")
        raise


def update_artifact_hashes(state: Dict[str, Any], project_root: Path) -> Dict[str, Any]:
    """
    Update artifact hashes in the state dictionary for data/raw and data/processed.

    Args:
        state: The current state dictionary.
        project_root: Root path of the project.

    Returns:
        Updated state dictionary.
    """
    import datetime

    data_raw_path = project_root / "data" / "raw"
    data_processed_path = project_root / "data" / "processed"

    raw_hashes = scan_directory_for_artifacts(data_raw_path)
    processed_hashes = scan_directory_for_artifacts(data_processed_path)

    if not raw_hashes:
        logger.info("No data to hash in data/raw")
    if not processed_hashes:
        logger.info("No data to hash in data/processed")

    state["artifact_hashes"]["data_raw"] = raw_hashes
    state["artifact_hashes"]["data_processed"] = processed_hashes
    state["last_updated"] = datetime.datetime.now().isoformat()

    return state


def verify_artifacts(state: Dict[str, Any], project_root: Path) -> bool:
    """
    Verify that artifacts in the state still exist and match their hashes.

    Args:
        state: The state dictionary containing hashes.
        project_root: Root path of the project.

    Returns:
        True if all artifacts match, False otherwise.
    """
    data_raw_path = project_root / "data" / "raw"
    data_processed_path = project_root / "data" / "processed"

    all_valid = True

    for rel_path, stored_hash in state["artifact_hashes"]["data_raw"].items():
        file_path = data_raw_path / rel_path
        if not file_path.exists():
            logger.warning(f"Artifact missing: {file_path}")
            all_valid = False
            continue
        current_hash = compute_file_hash(file_path)
        if current_hash != stored_hash:
            logger.warning(f"Hash mismatch for {file_path}")
            all_valid = False

    for rel_path, stored_hash in state["artifact_hashes"]["data_processed"].items():
        file_path = data_processed_path / rel_path
        if not file_path.exists():
            logger.warning(f"Artifact missing: {file_path}")
            all_valid = False
            continue
        current_hash = compute_file_hash(file_path)
        if current_hash != stored_hash:
            logger.warning(f"Hash mismatch for {file_path}")
            all_valid = False

    return all_valid


def main() -> None:
    """
    Main entry point for the state manager script.
    Performs a dry-run hash calculation on a dummy file to verify the update mechanism.
    """
    project_root = Path(__file__).resolve().parents[3]
    state_path = project_root / "state" / "projects" / "PROJ-006-agriculture-optimization.yaml"

    logger.info(f"Project root: {project_root}")
    logger.info(f"State path: {state_path}")

    # Ensure state file exists
    state = load_state(state_path)

    # Update hashes
    state = update_artifact_hashes(state, project_root)

    # Save updated state
    save_state(state, state_path)

    # Verify artifacts
    is_valid = verify_artifacts(state, project_root)
    if is_valid:
        logger.info("Artifact verification passed.")
    else:
        logger.warning("Artifact verification failed.")

    # Create dummy file for dry-run verification if it doesn't exist
    dummy_file = project_root / "data" / "raw" / "dummy.txt"
    if not dummy_file.exists():
        dummy_file.parent.mkdir(parents=True, exist_ok=True)
        with open(dummy_file, "w") as f:
            f.write("Dummy file for state manager verification.")
        logger.info(f"Created dummy file: {dummy_file}")

    # Re-scan to include dummy file
    state = update_artifact_hashes(state, project_root)
    save_state(state, state_path)

    logger.info("State manager dry-run completed successfully.")


if __name__ == "__main__":
    main()