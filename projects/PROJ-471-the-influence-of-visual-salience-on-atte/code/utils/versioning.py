import hashlib
import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import yaml

from config import get_paths

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


def _get_state_file_path() -> Path:
    """
    Get the path to the state.yaml file.

    Returns:
        Path to the state.yaml file in the project root.
    """
    paths = get_paths()
    return paths.root / "state.yaml"


def load_state() -> Dict[str, Any]:
    """
    Load the current state from state.yaml.

    Returns:
        Dictionary containing the current state.
        Returns an empty dict if the file does not exist.
    """
    state_file = _get_state_file_path()
    if not state_file.exists():
        logger.info(f"State file not found at {state_file}, starting fresh.")
        return {
            "version": "1.0.0",
            "last_updated": datetime.utcnow().isoformat(),
            "artifacts": {},
            "metadata": {
                "pipeline_runs": 0,
                "total_artifacts_registered": 0
            }
        }

    try:
        with open(state_file, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f)
            if state is None:
                return {
                    "version": "1.0.0",
                    "last_updated": datetime.utcnow().isoformat(),
                    "artifacts": {},
                    "metadata": {
                        "pipeline_runs": 0,
                        "total_artifacts_registered": 0
                    }
                }
            return state
    except yaml.YAMLError as e:
        logger.error(f"Error parsing state.yaml: {e}")
        raise
    except IOError as e:
        logger.error(f"Error reading state.yaml: {e}")
        raise


def save_state(state: Dict[str, Any]) -> None:
    """
    Save the state to state.yaml.

    Args:
        state: The state dictionary to save.
    """
    state_file = _get_state_file_path()
    state["last_updated"] = datetime.utcnow().isoformat()

    try:
        # Ensure directory exists
        state_file.parent.mkdir(parents=True, exist_ok=True)

        with open(state_file, "w", encoding="utf-8") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State saved to {state_file}")
    except IOError as e:
        logger.error(f"Error writing state.yaml: {e}")
        raise


def register_artifact(
    file_path: Path,
    artifact_type: str,
    description: str = "",
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Register an artifact in the state.yaml file.

    This function computes the SHA-256 hash of the file, creates a unique
    identifier for the artifact, and updates the state.yaml file with the
    artifact's information.

    Args:
        file_path: Path to the artifact file.
        artifact_type: Type of the artifact (e.g., 'model', 'dataset', 'log').
        description: Optional description of the artifact.
        tags: Optional list of tags for categorization.
        metadata: Optional additional metadata dictionary.

    Returns:
        Dictionary containing the artifact registration details.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file path is invalid.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact file not found: {file_path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    # Compute hash
    file_hash = compute_sha256(file_path)
    file_size = file_path.stat().st_size
    file_name = file_path.name
    relative_path = str(file_path.relative_to(get_paths().root))

    # Create artifact ID
    artifact_id = f"{artifact_type}_{file_name}_{file_hash[:8]}"

    artifact_entry = {
        "id": artifact_id,
        "path": relative_path,
        "hash": file_hash,
        "type": artifact_type,
        "size_bytes": file_size,
        "description": description,
        "tags": tags or [],
        "metadata": metadata or {},
        "registered_at": datetime.utcnow().isoformat()
    }

    # Load current state
    state = load_state()

    # Add to artifacts dictionary
    if "artifacts" not in state:
        state["artifacts"] = {}

    state["artifacts"][artifact_id] = artifact_entry

    # Update metadata
    if "metadata" not in state:
        state["metadata"] = {"pipeline_runs": 0, "total_artifacts_registered": 0}

    state["metadata"]["total_artifacts_registered"] = state["metadata"].get("total_artifacts_registered", 0) + 1

    # Save updated state
    save_state(state)

    logger.info(f"Artifact registered: {artifact_id} ({file_name})")
    return artifact_entry


def verify_artifact_integrity(file_path: Path, expected_hash: str) -> bool:
    """
    Verify the integrity of an artifact by comparing its hash.

    Args:
        file_path: Path to the artifact file.
        expected_hash: Expected SHA-256 hash of the file.

    Returns:
        True if the hash matches, False otherwise.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    actual_hash = compute_sha256(file_path)
    return actual_hash == expected_hash


def get_artifact_by_hash(file_hash: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve an artifact's information by its hash.

    Args:
        file_hash: SHA-256 hash of the artifact.

    Returns:
        Dictionary containing artifact information, or None if not found.
    """
    state = load_state()
    artifacts = state.get("artifacts", {})

    for artifact_id, artifact_data in artifacts.items():
        if artifact_data.get("hash") == file_hash:
            return artifact_data

    return None
