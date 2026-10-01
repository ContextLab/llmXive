"""
State Manager for llmXive project.
Computes SHA-256 hashes for artifacts and updates the project state file.
"""
import hashlib
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import yaml

STATE_FILE_PATH = Path("state/project_state.yaml")

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
        StateError: If the file does not exist or cannot be read.
    """
    path = Path(file_path)
    if not path.exists():
        raise StateError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
    except IOError as e:
        raise StateError(f"Error reading file {file_path}: {e}")

    return sha256_hash.hexdigest()

def load_state() -> Dict[str, Any]:
    """
    Load the project state from the YAML file.

    Returns:
        Dictionary containing the project state.
    """
    if not STATE_FILE_PATH.exists():
        return {"artifacts": {}}

    try:
        with open(STATE_FILE_PATH, "r") as f:
            state = yaml.safe_load(f)
            if state is None:
                return {"artifacts": {}}
            if "artifacts" not in state:
                state["artifacts"] = {}
            return state
    except yaml.YAMLError as e:
        raise StateError(f"Error parsing state file {STATE_FILE_PATH}: {e}")
    except IOError as e:
        raise StateError(f"Error reading state file {STATE_FILE_PATH}: {e}")

def save_state(state: Dict[str, Any]) -> None:
    """
    Save the project state to the YAML file.

    Args:
        state: Dictionary containing the project state.
    """
    # Ensure the directory exists
    STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(STATE_FILE_PATH, "w") as f:
        yaml.safe_dump(state, f, default_flow_style=False, sort_keys=False)

def update_artifact_state(file_path: str, state: Dict[str, Any]) -> None:
    """
    Update the state entry for a single artifact.

    Args:
        file_path: Path to the artifact.
        state: The current state dictionary (modified in place).
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    file_hash = compute_sha256(file_path)

    if "artifacts" not in state:
        state["artifacts"] = {}

    state["artifacts"][file_path] = {
        "hash": file_hash,
        "timestamp": timestamp
    }

def update_state_for_multiple_artifacts(file_paths: List[str]) -> Dict[str, Any]:
    """
    Update the state for multiple artifacts at once.

    Args:
        file_paths: List of file paths to update.

    Returns:
        The updated state dictionary.
    """
    state = load_state()
    for path in file_paths:
        update_artifact_state(path, state)
    save_state(state)
    return state

def verify_artifact(file_path: str) -> bool:
    """
    Verify the integrity of an artifact by comparing its current hash
    with the one stored in the state file.

    Args:
        file_path: Path to the artifact.

    Returns:
        True if the hash matches, False otherwise.
    """
    state = load_state()
    if file_path not in state.get("artifacts", {}):
        # If the file is not in state, we can't verify it
        return False

    stored_hash = state["artifacts"][file_path].get("hash")
    if not stored_hash:
        return False

    current_hash = compute_sha256(file_path)
    return current_hash == stored_hash

def compute_and_update_hash(file_path: str) -> None:
    """
    Compute the SHA-256 hash for a given file and update the
    state/project_state.yaml file with the file path, hash, and timestamp.

    Args:
        file_path: Path to the file to hash.

    Raises:
        StateError: If the file cannot be hashed or the state cannot be updated.
    """
    state = load_state()
    update_artifact_state(file_path, state)
    save_state(state)

def main() -> None:
    """
    CLI entry point for the state manager.
    Usage: python -m code.utils.state_manager <update|verify> <file_path>
    """
    if len(sys.argv) < 3:
        print("Usage: python -m code.utils.state_manager <update|verify> <file_path>")
        sys.exit(1)

    command = sys.argv[1]
    target_file = sys.argv[2]

    try:
        if command == "update":
            compute_and_update_hash(target_file)
            print(f"Updated state for: {target_file}")
        elif command == "verify":
            is_valid = verify_artifact(target_file)
            if is_valid:
                print(f"Verification PASSED for: {target_file}")
            else:
                print(f"Verification FAILED for: {target_file}")
                sys.exit(1)
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    except StateError as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
