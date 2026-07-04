"""
State management utility for llmXive project PROJ-206.

This module provides functionality to compute SHA-256 hashes of files
and update the project state YAML file located at
`state/projects/PROJ-206-*.yaml` upon creation of derived artifacts.
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from src.utils.config import get_project_root, get_state_path


def compute_file_hash(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string representation of the SHA-256 hash.

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
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def get_state_file_path() -> Path:
    """
    Determine the path to the project state YAML file.

    Returns:
        Path to the state file (e.g., state/projects/PROJ-206-state.yaml).
    """
    state_dir = get_state_path()
    # Ensure the directory exists
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / "PROJ-206-state.yaml"


def load_state() -> Dict[str, Any]:
    """
    Load the current state from the YAML file.

    Returns:
        Dictionary containing the current state. Returns an empty dict
        if the file does not exist or is empty.
    """
    state_file = get_state_file_path()
    if not state_file.exists():
        return {}

    try:
        with open(state_file, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
            return content if content else {}
    except yaml.YAMLError:
        # If YAML is corrupted, return empty state to avoid crashes
        return {}


def save_state(state: Dict[str, Any]) -> None:
    """
    Save the state dictionary to the YAML file.

    Args:
        state: Dictionary to save.
    """
    state_file = get_state_file_path()
    state_file.parent.mkdir(parents=True, exist_ok=True)

    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)


def update_artifact_state(artifact_path: Path, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Compute the hash of an artifact and update the project state file.

    This function:
    1. Computes the SHA-256 hash of the provided artifact.
    2. Loads the current state.
    3. Updates the 'artifacts' section with the new hash and metadata.
    4. Saves the updated state back to disk.

    Args:
        artifact_path: Absolute or relative path to the generated artifact.
        description: Optional human-readable description of the artifact.

    Returns:
        The updated state dictionary.

    Raises:
        FileNotFoundError: If the artifact does not exist.
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")

    # Ensure path is relative to project root for storage
    project_root = get_project_root()
    try:
        relative_path = artifact_path.relative_to(project_root)
    except ValueError:
        # If not relative, use absolute path string
        relative_path = artifact_path

    file_hash = compute_file_hash(artifact_path)
    state = load_state()

    if "artifacts" not in state:
        state["artifacts"] = {}

    artifact_entry = {
        "path": str(relative_path),
        "hash": file_hash,
        "description": description or f"Derived artifact: {relative_path}",
    }

    state["artifacts"][str(relative_path)] = artifact_entry

    save_state(state)
    return state


def verify_artifact_integrity(artifact_path: Path) -> bool:
    """
    Verify the integrity of an artifact against the stored hash in the state file.

    Args:
        artifact_path: Path to the artifact to verify.

    Returns:
        True if the hash matches, False otherwise.
    """
    if not artifact_path.exists():
        return False

    project_root = get_project_root()
    try:
        relative_path = artifact_path.relative_to(project_root)
    except ValueError:
        relative_path = artifact_path

    state = load_state()
    stored_entry = state.get("artifacts", {}).get(str(relative_path))

    if not stored_entry or "hash" not in stored_entry:
        return False

    current_hash = compute_file_hash(artifact_path)
    return current_hash == stored_entry["hash"]
