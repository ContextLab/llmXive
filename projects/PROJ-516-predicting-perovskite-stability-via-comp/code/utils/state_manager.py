"""
State manager for computing SHA-256 hashes of artifacts and updating project state.
"""
import hashlib
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_FILE = PROJECT_ROOT / "state" / "project_state.yaml"


class StateError(Exception):
    """Custom exception for state management errors."""
    pass


def compute_sha256(file_path: str) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        StateError: If the file cannot be read.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise StateError(f"Failed to read file {file_path}: {e}")


def load_state() -> Dict[str, Any]:
    """
    Load the current project state from the YAML file.

    Returns:
        Dictionary containing the project state.
    """
    if not STATE_FILE.exists():
        return {"artifacts": {}}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f)
            if state is None:
                return {"artifacts": {}}
            return state
    except yaml.YAMLError as e:
        raise StateError(f"Failed to parse state file {STATE_FILE}: {e}")


def save_state(state: Dict[str, Any]) -> None:
    """
    Save the project state to the YAML file.

    Args:
        state: Dictionary containing the project state.
    """
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        yaml.safe_dump(state, f, default_flow_style=False, sort_keys=False)


def update_artifact_state(file_path: str, hash_value: str, state: Dict[str, Any]) -> None:
    """
    Update the state dictionary with a new artifact entry.

    Args:
        file_path: Relative path of the artifact.
        hash_value: SHA-256 hash of the artifact.
        state: The state dictionary to update.
    """
    if "artifacts" not in state:
        state["artifacts"] = {}

    timestamp = datetime.now(timezone.utc).isoformat()

    state["artifacts"][file_path] = {
        "hash": hash_value,
        "timestamp": timestamp
    }


def update_state_for_multiple_artifacts(files: List[str], state: Dict[str, Any]) -> None:
    """
    Update state for multiple files at once.

    Args:
        files: List of file paths to hash and record.
        state: The state dictionary to update.
    """
    for f in files:
        try:
            h = compute_sha256(f)
            update_artifact_state(f, h, state)
        except FileNotFoundError:
            # Log warning but continue
            import logging
            logging.warning(f"Skipping missing file for state update: {f}")


def compute_and_update_hash(file_path: str) -> None:
    """
    Compute the SHA-256 hash for a file and update the project state file.

    This function reads the current state, computes the hash for the specified
    file, updates the 'artifacts' section with the new hash and timestamp,
    and writes the updated state back to disk.

    Args:
        file_path: Path to the file (relative to project root) to hash and record.

    Raises:
        FileNotFoundError: If the file does not exist.
        StateError: If state file operations fail.
    """
    # Ensure absolute path for hashing, but store relative path
    full_path = Path(file_path)
    if not full_path.is_absolute():
        full_path = PROJECT_ROOT / file_path

    # Compute hash
    hash_value = compute_sha256(str(full_path))

    # Load current state
    state = load_state()

    # Update state with the new entry
    update_artifact_state(file_path, hash_value, state)

    # Save updated state
    save_state(state)


def verify_artifact(file_path: str) -> bool:
    """
    Verify the integrity of an artifact by comparing its current hash
    with the hash stored in the project state.

    Args:
        file_path: Path to the artifact to verify.

    Returns:
        True if the artifact's hash matches the stored hash, False otherwise.
    """
    state = load_state()
    if "artifacts" not in state or file_path not in state["artifacts"]:
        return False

    stored_hash = state["artifacts"][file_path]["hash"]
    try:
        current_hash = compute_sha256(file_path)
        return current_hash == stored_hash
    except FileNotFoundError:
        return False


def main():
    """
    Command-line interface for the state manager.
    Usage: python -m code.utils.state_manager <update|verify> <file_path>
    """
    if len(sys.argv) < 3:
        print("Usage: python -m code.utils.state_manager <update|verify> <file_path>")
        sys.exit(1)

    command = sys.argv[1]
    file_path = sys.argv[2]

    if command == "update":
        try:
            compute_and_update_hash(file_path)
            print(f"Updated state for: {file_path}")
        except Exception as e:
            print(f"Error updating state: {e}")
            sys.exit(1)
    elif command == "verify":
        if verify_artifact(file_path):
            print(f"Verification successful for: {file_path}")
            sys.exit(0)
        else:
            print(f"Verification failed for: {file_path}")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()