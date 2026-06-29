"""State tracking utilities for artifact hash computation and state file updates.

This module provides functions to:
- Compute SHA-256 hashes for artifacts (files and directories)
- Load and save state YAML files
- Update state files with artifact hashes and timestamps
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from checksum import compute_sha256, compute_directory_checksums


def compute_file_hash(file_path: Union[str, Path]) -> str:
    """Compute SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal SHA-256 hash string.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    return compute_sha256(file_path)


def compute_directory_hash(dir_path: Union[str, Path]) -> str:
    """Compute hash for a directory by hashing all files within it.

    Args:
        dir_path: Path to the directory to hash.

    Returns:
        Combined hash string for all files in the directory.

    Raises:
        NotADirectoryError: If the path is not a directory.
    """
    return compute_directory_checksums(dir_path)


def load_state_file(state_path: Union[str, Path]) -> Dict[str, Any]:
    """Load the state YAML file, creating it if it doesn't exist.

    Args:
        state_path: Path to the state YAML file.

    Returns:
        State dictionary with 'state' key containing state data.
    """
    state_path = Path(state_path)
    if not state_path.exists():
        return {"state": {}}
    with open(state_path, 'r') as f:
        content = yaml.safe_load(f)
        return content if content else {"state": {}}


def save_state_file(state_path: Union[str, Path], state: Dict[str, Any]) -> None:
    """Save the state dictionary to a YAML file.

    Args:
        state_path: Path to the state YAML file.
        state: State dictionary to save.
    """
    state_path = Path(state_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)


def update_state_with_artifact(
    state_path: Union[str, Path],
    artifact_path: Union[str, Path],
    artifact_name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Update state file with artifact hash and timestamp.

    Args:
        state_path: Path to the state YAML file.
        artifact_path: Path to the artifact to hash.
        artifact_name: Optional name for the artifact (defaults to filename).
        metadata: Optional additional metadata to store.

    Returns:
        Updated state dictionary.
    """
    state = load_state_file(state_path)

    if "state" not in state:
        state["state"] = {}

    if "artifacts" not in state["state"]:
        state["state"]["artifacts"] = {}

    # Get artifact name
    if artifact_name is None:
        artifact_name = Path(artifact_path).name

    # Compute hash
    artifact_path = Path(artifact_path)
    if artifact_path.exists():
        file_hash = compute_file_hash(artifact_path)
    else:
        file_hash = None

    # Update timestamp
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Store artifact info
    state["state"]["artifacts"][artifact_name] = {
        "path": str(artifact_path),
        "hash": file_hash,
        "updated_at": timestamp,
        "type": "file" if artifact_path.is_file() else "directory",
        **(metadata or {})
    }

    # Update global timestamp
    state["state"]["updated_at"] = timestamp

    # Save state
    save_state_file(state_path, state)

    return state


def update_state_timestamp(
    state_path: Union[str, Path],
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Update state file with current timestamp.

    Args:
        state_path: Path to the state YAML file.
        metadata: Optional additional metadata to store.

    Returns:
        Updated state dictionary.
    """
    state = load_state_file(state_path)

    if "state" not in state:
        state["state"] = {}

    timestamp = datetime.utcnow().isoformat() + "Z"
    state["state"]["updated_at"] = timestamp

    if metadata:
        if "metadata" not in state["state"]:
            state["state"]["metadata"] = {}
        state["state"]["metadata"].update(metadata)

    save_state_file(state_path, state)

    return state


def register_artifact_hash(
    state_path: Union[str, Path],
    artifact_path: Union[str, Path],
    artifact_type: str = "file"
) -> Dict[str, Any]:
    """Register an artifact hash in the state file.

    This is a convenience wrapper around update_state_with_artifact
    that automatically determines the artifact name from the path.

    Args:
        state_path: Path to the state YAML file.
        artifact_path: Path to the artifact to register.
        artifact_type: Type of artifact ('file' or 'directory').

    Returns:
        Updated state dictionary.
    """
    return update_state_with_artifact(
        state_path,
        artifact_path,
        metadata={"type": artifact_type}
    )


def get_artifact_state(
    state_path: Union[str, Path],
    artifact_name: str
) -> Optional[Dict[str, Any]]:
    """Get the state information for a specific artifact.

    Args:
        state_path: Path to the state YAML file.
        artifact_name: Name of the artifact to look up.

    Returns:
        Artifact state dictionary or None if not found.
    """
    state = load_state_file(state_path)
    artifacts = state.get("state", {}).get("artifacts", {})
    return artifacts.get(artifact_name)


def verify_artifact_integrity(
    state_path: Union[str, Path],
    artifact_name: str,
    expected_path: Optional[Union[str, Path]] = None
) -> bool:
    """Verify that an artifact's current hash matches the stored hash.

    Args:
        state_path: Path to the state YAML file.
        artifact_name: Name of the artifact to verify.
        expected_path: Optional path override for the artifact.

    Returns:
        True if hash matches or artifact not found, False otherwise.
    """
    artifact_state = get_artifact_state(state_path, artifact_name)
    if artifact_state is None:
        return True  # Artifact not in state, nothing to verify

    stored_hash = artifact_state.get("hash")
    if stored_hash is None:
        return True  # No hash stored, nothing to verify

    path_to_check = expected_path or artifact_state.get("path")
    if path_to_check is None:
        return False

    current_hash = compute_file_hash(path_to_check)
    return current_hash == stored_hash


def main():
    """Main function for testing and demonstration."""
    project_id = "PROJ-488-evaluating-the-impact-of-code-generation"
    state_path = Path("state/projects") / f"{project_id}.yaml"

    # Ensure directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a test artifact
    test_file = Path("data/test_artifact.txt")
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("Test content for state tracking")

    # Update state with the artifact
    state = update_state_with_artifact(
        state_path,
        test_file,
        "test_artifact",
        {"description": "Test artifact for state tracking", "phase": "T006"}
    )

    print(f"State updated successfully: {state_path}")
    print(f"Artifacts registered: {list(state['state']['artifacts'].keys())}")
    print(f"Last updated: {state['state']['updated_at']}")

    # Verify the artifact
    is_valid = verify_artifact_integrity(state_path, "test_artifact")
    print(f"Artifact integrity verified: {is_valid}")


if __name__ == "__main__":
    main()
