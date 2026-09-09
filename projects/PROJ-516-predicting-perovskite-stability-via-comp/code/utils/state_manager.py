"""
State Manager Module (T004)

Computes SHA-256 hashes for derived artifacts and updates the project state file.
This module ensures traceability and reproducibility by maintaining a manifest
of artifact hashes in state/artifacts.yaml.
"""

import hashlib
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

import yaml

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

STATE_FILE = PROJECT_ROOT / "state" / "artifacts.yaml"


class StateError(Exception):
    """Custom exception for state management errors."""
    pass


def compute_sha256(file_path: Path) -> str:
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
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
    except IOError as e:
        raise StateError(f"Error reading file {file_path}: {e}")

    return sha256_hash.hexdigest()


def load_state() -> Dict[str, Any]:
    """
    Load the current state file.

    Returns:
        Dictionary containing the state data. Returns empty structure if file missing.
    """
    if not STATE_FILE.exists():
        return {
            "last_updated": None,
            "artifacts": {}
        }

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {"artifacts": {}}
    except yaml.YAMLError as e:
        raise StateError(f"Error parsing state file {STATE_FILE}: {e}")


def save_state(state: Dict[str, Any]) -> None:
    """
    Save the state dictionary to the state file.

    Args:
        state: The state dictionary to save.
    """
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    except IOError as e:
        raise StateError(f"Error writing state file {STATE_FILE}: {e}")


def update_artifact_state(file_path: Path, state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Update the state for a single artifact.

    Computes the hash of the file and updates the state dictionary.
    If no state is provided, loads the current state first.

    Args:
        file_path: Path to the artifact file.
        state: Optional existing state dictionary.

    Returns:
        Updated state dictionary.
    """
    if state is None:
        state = load_state()

    if not file_path.exists():
        raise FileNotFoundError(f"Cannot update state for missing file: {file_path}")

    file_hash = compute_sha256(file_path)
    relative_path = str(file_path.relative_to(PROJECT_ROOT))

    if "artifacts" not in state:
        state["artifacts"] = {}

    state["artifacts"][relative_path] = {
        "hash": file_hash,
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }

    state["last_updated"] = datetime.utcnow().isoformat() + "Z"

    save_state(state)
    return state


def update_state_for_multiple_artifacts(file_paths: List[Path]) -> Dict[str, Any]:
    """
    Update the state for multiple artifacts at once.

    Args:
        file_paths: List of paths to artifact files.

    Returns:
        Updated state dictionary.
    """
    state = load_state()
    for path in file_paths:
        update_artifact_state(path, state)
    return state


def verify_artifact(file_path: Path) -> bool:
    """
    Verify the integrity of an artifact by comparing its current hash with the stored hash.

    Args:
        file_path: Path to the artifact file.

    Returns:
        True if the hash matches, False otherwise.

    Raises:
        FileNotFoundError: If the file or state file is missing.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for verification: {file_path}")

    state = load_state()
    relative_path = str(file_path.relative_to(PROJECT_ROOT))

    if relative_path not in state.get("artifacts", {}):
        return False

    stored_hash = state["artifacts"][relative_path].get("hash")
    if not stored_hash:
        return False

    current_hash = compute_sha256(file_path)
    return current_hash == stored_hash


def main():
    """
    CLI entry point for state manager.

    Usage:
        python -m code.utils.state_manager <update|verify> <file_path>

    Examples:
        python -m code.utils.state_manager update data/processed/descriptors_final.csv
        python -m code.utils.state_manager verify data/processed/descriptors_final.csv
    """
    if len(sys.argv) < 3:
        print("Usage: python -m code.utils.state_manager <update|verify> <file_path>")
        sys.exit(1)

    command = sys.argv[1].lower()
    file_arg = sys.argv[2]
    file_path = PROJECT_ROOT / file_arg

    try:
        if command == "update":
            update_artifact_state(file_path)
            print(f"State updated for: {file_path}")
        elif command == "verify":
            is_valid = verify_artifact(file_path)
            if is_valid:
                print(f"Verification passed for: {file_path}")
            else:
                print(f"Verification failed for: {file_path}")
                sys.exit(1)
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except StateError as e:
        print(f"State Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()