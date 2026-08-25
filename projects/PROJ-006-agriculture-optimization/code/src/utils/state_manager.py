import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml

logger = logging.getLogger(__name__)

PROJECT_STATE_PATH = Path("state/projects/PROJ-006-agriculture-optimization.yaml")
DATA_RAW_PATH = Path("data/raw")
DATA_PROCESSED_PATH = Path("data/processed")


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def scan_directory_for_artifacts(directory: Path) -> Dict[str, str]:
    """
    Scan a directory recursively for files and compute their hashes.
    Returns a dict mapping relative path (from directory) to SHA-256 hash.
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist, skipping: {directory}")
        return {}

    artifacts = {}
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(directory))
            try:
                file_hash = compute_file_hash(file_path)
                artifacts[rel_path] = file_hash
            except Exception as e:
                logger.error(f"Failed to hash {file_path}: {e}")
    return artifacts


def load_state(state_path: Path) -> Dict[str, Any]:
    """Load state from YAML file, returning empty dict if missing."""
    if not state_path.exists():
        return {"projects": {}}
    try:
        with open(state_path, "r") as f:
            return yaml.safe_load(f) or {"projects": {}}
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse state file {state_path}: {e}")
        return {"projects": {}}


def save_state(state_path: Path, state: Dict[str, Any]) -> None:
    """Save state to YAML file."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w") as f:
        yaml.safe_dump(state, f, sort_keys=False)


def update_artifact_hashes(project_id: str = "PROJ-006-agriculture-optimization") -> Dict[str, Any]:
    """
    Scan data/raw and data/processed, compute hashes, and update the project state.
    Returns the updated project state entry.
    """
    state = load_state(PROJECT_STATE_PATH)
    if "projects" not in state:
        state["projects"] = {}

    project_state = state["projects"].get(project_id, {})

    raw_hashes = scan_directory_for_artifacts(DATA_RAW_PATH)
    processed_hashes = scan_directory_for_artifacts(DATA_PROCESSED_PATH)

    project_state["last_updated"] = None  # Could add timestamp logic if needed
    project_state["data_raw"] = raw_hashes
    project_state["data_processed"] = processed_hashes

    state["projects"][project_id] = project_state
    save_state(PROJECT_STATE_PATH, state)

    logger.info(f"Updated state for project {project_id}. Raw: {len(raw_hashes)}, Processed: {len(processed_hashes)}")
    return project_state


def verify_artifacts(project_id: str = "PROJ-006-agriculture-optimization") -> bool:
    """
    Verify that current file hashes match the stored state.
    Returns True if all match (or if state is empty/new), False otherwise.
    """
    state = load_state(PROJECT_STATE_PATH)
    project_state = state.get("projects", {}).get(project_id)

    if not project_state:
        logger.info("No previous state found, verification skipped.")
        return True

    # Re-scan current state
    current_raw = scan_directory_for_artifacts(DATA_RAW_PATH)
    current_processed = scan_directory_for_artifacts(DATA_PROCESSED_PATH)

    stored_raw = project_state.get("data_raw", {})
    stored_processed = project_state.get("data_processed", {})

    # Check raw
    if set(current_raw.keys()) != set(stored_raw.keys()):
        logger.warning("Raw data file set changed.")
        return False
    for path, hash_val in current_raw.items():
        if stored_raw.get(path) != hash_val:
            logger.warning(f"Hash mismatch for raw file: {path}")
            return False

    # Check processed
    if set(current_processed.keys()) != set(stored_processed.keys()):
        logger.warning("Processed data file set changed.")
        return False
    for path, hash_val in current_processed.items():
        if stored_processed.get(path) != hash_val:
            logger.warning(f"Hash mismatch for processed file: {path}")
            return False

    logger.info("Artifact verification passed.")
    return True


def main() -> None:
    """CLI entry point to update and verify artifact hashes."""
    logging.basicConfig(level=logging.INFO)
    project_id = "PROJ-006-agriculture-optimization"
    logger.info(f"Updating artifact hashes for project: {project_id}")
    update_artifact_hashes(project_id)
    logger.info("Verifying artifacts...")
    if verify_artifacts(project_id):
        logger.info("Verification successful.")
    else:
        logger.error("Verification failed.")


if __name__ == "__main__":
    main()
