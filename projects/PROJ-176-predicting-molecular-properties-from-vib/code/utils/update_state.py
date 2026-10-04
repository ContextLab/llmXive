"""
State management utilities for tracking artifact integrity and task completion.
Implements Principle V for reproducible state tracking.
"""
import hashlib
import os
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state(state_file: Path) -> Dict[str, Any]:
    """
    Load state from a YAML file.

    Args:
        state_file: Path to the state YAML file.

    Returns:
        Dictionary containing the state.
    """
    if not state_file.exists():
        return {"artifacts": {}, "tasks": {}, "metadata": {}}

    with open(state_file, "r") as f:
        return yaml.safe_load(f) or {"artifacts": {}, "tasks": {}, "metadata": {}}

def save_state(state: Dict[str, Any], state_file: Path) -> None:
    """
    Save state to a YAML file.

    Args:
        state: State dictionary to save.
        state_file: Path to the state YAML file.
    """
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, "w") as f:
        yaml.safe_dump(state, f, default_flow_style=False)

def update_artifact_state(
    state: Dict[str, Any],
    artifact_name: str,
    artifact_path: Path,
    task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update state with information about a generated artifact.

    Args:
        state: Current state dictionary.
        artifact_name: Name of the artifact.
        artifact_path: Path to the artifact file.
        task_id: Optional ID of the task that generated the artifact.

    Returns:
        Updated state dictionary.
    """
    if "artifacts" not in state:
        state["artifacts"] = {}

    if artifact_path.exists():
        file_hash = compute_sha256(artifact_path)
        file_size = artifact_path.stat().st_size
        timestamp = datetime.now().isoformat()

        state["artifacts"][artifact_name] = {
            "path": str(artifact_path),
            "hash": file_hash,
            "size_bytes": file_size,
            "timestamp": timestamp,
            "task_id": task_id
        }
    else:
        state["artifacts"][artifact_name] = {
            "path": str(artifact_path),
            "hash": None,
            "size_bytes": 0,
            "timestamp": timestamp,
            "task_id": task_id,
            "status": "missing"
        }

    return state

def update_task_state(
    state: Dict[str, Any],
    task_id: str,
    status: str = "completed",
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Update state with task completion information.

    Args:
        state: Current state dictionary.
        task_id: ID of the task.
        status: Task status (e.g., "completed", "failed", "in_progress").
        details: Optional additional details about the task.

    Returns:
        Updated state dictionary.
    """
    if "tasks" not in state:
        state["tasks"] = {}

    state["tasks"][task_id] = {
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    }

    return state

def hash_multiple_artifacts(
    artifact_paths: List[Path],
    state: Dict[str, Any]
) -> Dict[str, str]:
    """
    Compute hashes for multiple artifacts and update state.

    Args:
        artifact_paths: List of paths to artifact files.
        state: Current state dictionary.

    Returns:
        Dictionary mapping artifact names to their hashes.
    """
    hashes = {}
    for path in artifact_paths:
        if path.exists():
          artifact_name = path.stem
          file_hash = compute_sha256(path)
          hashes[artifact_name] = file_hash
          state = update_artifact_state(state, artifact_name, path)
    return hashes

def get_artifact_hash(state: Dict[str, Any], artifact_name: str) -> Optional[str]:
    """
    Get the hash of a specific artifact from state.

    Args:
        state: State dictionary.
        artifact_name: Name of the artifact.

    Returns:
        Hash string or None if not found.
    """
    if "artifacts" in state and artifact_name in state["artifacts"]:
        return state["artifacts"][artifact_name].get("hash")
    return None

def verify_artifact_integrity(
    artifact_path: Path,
    expected_hash: str
) -> bool:
    """
    Verify that an artifact matches its expected hash.

    Args:
        artifact_path: Path to the artifact file.
        expected_hash: Expected SHA-256 hash.

    Returns:
        True if the artifact matches the expected hash, False otherwise.
    """
    if not artifact_path.exists():
        return False

    actual_hash = compute_sha256(artifact_path)
    return actual_hash == expected_hash

def main():
    """
    Main entry point for state management CLI.
    This is a placeholder for future CLI functionality.
    """
    print("State management utilities loaded successfully.")
    print("Use update_artifact_state, update_task_state, and related functions to manage project state.")

if __name__ == "__main__":
    main()
