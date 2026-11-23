"""
State Manager Module for llmXive Project.

Provides functionality to compute SHA-256 hashes for derived artifacts
and update the project state file (state/project_state.yaml).
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


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
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
    except IOError as e:
        raise StateError(f"Error reading file {file_path}: {e}")

    return sha256_hash.hexdigest()


def load_state(state_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the project state from the YAML file.

    Args:
        state_path: Optional path to the state file. Defaults to 'state/project_state.yaml'.

    Returns:
        Dictionary containing the project state.
    """
    if state_path is None:
        state_path = "state/project_state.yaml"

    path = Path(state_path)
    if not path.exists():
        return {"artifacts": {}}

    try:
        with open(path, "r") as f:
            state = yaml.safe_load(f)
            if state is None:
                return {"artifacts": {}}
            return state
    except yaml.YAMLError as e:
        raise StateError(f"Error parsing state file {state_path}: {e}")
    except IOError as e:
        raise StateError(f"Error reading state file {state_path}: {e}")


def save_state(state: Dict[str, Any], state_path: Optional[str] = None) -> None:
    """
    Save the project state to the YAML file.

    Args:
        state: Dictionary containing the project state.
        state_path: Optional path to the state file. Defaults to 'state/project_state.yaml'.
    """
    if state_path is None:
        state_path = "state/project_state.yaml"

    path = Path(state_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(path, "w") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    except IOError as e:
        raise StateError(f"Error writing state file {state_path}: {e}")


def update_artifact_state(
    state: Dict[str, Any],
    file_path: str,
    hash_val: str,
    timestamp: Optional[str] = None
) -> None:
    """
    Update the state dictionary with a new artifact entry.

    Args:
        state: The state dictionary to update (modified in place).
        file_path: Path of the artifact.
        hash_val: SHA-256 hash of the artifact.
        timestamp: ISO-8601 timestamp. Defaults to current UTC time.
    """
    if "artifacts" not in state:
        state["artifacts"] = {}

    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()

    state["artifacts"][file_path] = {
        "hash": hash_val,
        "timestamp": timestamp
    }


def update_state_for_multiple_artifacts(
    file_paths: list,
    state_path: Optional[str] = None
) -> None:
    """
    Update the state file with hashes for multiple artifacts.

    Args:
        file_paths: List of file paths to hash and record.
        state_path: Optional path to the state file.
    """
    state = load_state(state_path)
    for f_path in file_paths:
        hash_val = compute_sha256(f_path)
        update_artifact_state(state, f_path, hash_val)
    save_state(state, state_path)


def compute_and_update_hash(file_path: str, state_path: Optional[str] = None) -> None:
    """
    Compute SHA-256 hash for a file and update the project state.

    This function computes the hash of the specified file and records the
    file path, hash, and current timestamp in the project state YAML file.

    Args:
        file_path: Path to the file to hash.
        state_path: Optional path to the state file. Defaults to 'state/project_state.yaml'.
    """
    state = load_state(state_path)
    hash_val = compute_sha256(file_path)
    update_artifact_state(state, file_path, hash_val)
    save_state(state, state_path)


def verify_artifact(file_path: str, expected_hash: str, state_path: Optional[str] = None) -> bool:
    """
    Verify that a file's hash matches the expected hash.

    Args:
        file_path: Path to the file to verify.
        expected_hash: Expected SHA-256 hash.
        state_path: Optional path to the state file.

    Returns:
        True if the hash matches, False otherwise.
    """
    actual_hash = compute_sha256(file_path)
    return actual_hash == expected_hash


def main() -> None:
    """
    CLI entry point for state_manager.
    Usage: python -m code.utils.state_manager <update|verify> <file_path>
    """
    if len(sys.argv) < 3:
        print("Usage: python -m code.utils.state_manager <update|verify> <file_path>")
        sys.exit(1)

    action = sys.argv[1]
    file_path = sys.argv[2]

    if action == "update":
        try:
            compute_and_update_hash(file_path)
            print(f"Updated state for {file_path}")
        except StateError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif action == "verify":
        state = load_state()
        if file_path not in state.get("artifacts", {}):
            print(f"Error: {file_path} not found in state.", file=sys.stderr)
            sys.exit(1)
        expected_hash = state["artifacts"][file_path]["hash"]
        if verify_artifact(file_path, expected_hash):
            print(f"Verification passed for {file_path}")
        else:
            print(f"Verification failed for {file_path}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Unknown action: {action}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
