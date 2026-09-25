"""
State Manager for llmXive pipeline.

Computes SHA-256 hashes for derived artifacts and updates the state
tracking YAML file to ensure reproducibility and integrity.
"""

import hashlib
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import yaml

# Project root is assumed to be the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_FILE_PATH = PROJECT_ROOT / "state" / "pipeline_state.yaml"


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
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise StateError(f"Error reading file {file_path}: {e}")


def load_state(state_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the current state from the YAML file.

    Args:
        state_path: Optional path to the state file. Defaults to PROJECT_ROOT/state/pipeline_state.yaml.

    Returns:
        Dictionary containing the state data. Returns an empty dict if the file does not exist.
    """
    if state_path is None:
        state_path = STATE_FILE_PATH

    if not state_path.exists():
        return {}

    try:
        with open(state_path, "r") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise StateError(f"Error parsing state file {state_path}: {e}")
    except IOError as e:
        raise StateError(f"Error reading state file {state_path}: {e}")


def save_state(state: Dict[str, Any], state_path: Optional[Path] = None) -> None:
    """
    Save the state dictionary to the YAML file.

    Args:
        state: Dictionary containing the state data.
        state_path: Optional path to the state file. Defaults to PROJECT_ROOT/state/pipeline_state.yaml.
    """
    if state_path is None:
        state_path = STATE_FILE_PATH

    # Ensure the directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(state_path, "w") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    except IOError as e:
        raise StateError(f"Error writing state file {state_path}: {e}")


def update_artifact_state(
    artifact_path: Path,
    state_path: Optional[Path] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compute the hash of an artifact and update the state file with the new hash and metadata.

    Args:
        artifact_path: Path to the artifact file.
        state_path: Optional path to the state file.
        description: Optional description of the artifact.

    Returns:
        The updated state dictionary.
    """
    state = load_state(state_path)

    if "artifacts" not in state:
        state["artifacts"] = {}

    rel_path = str(artifact_path.relative_to(PROJECT_ROOT))

    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact file not found: {artifact_path}")

    file_hash = compute_sha256(artifact_path)

    state["artifacts"][rel_path] = {
        "hash": file_hash,
        "updated_at": datetime.now().isoformat(),
        "description": description or f"Auto-generated hash for {rel_path}"
    }

    save_state(state, state_path)
    return state


def update_state_for_multiple_artifacts(
    artifact_paths: List[Path],
    state_path: Optional[Path] = None,
    descriptions: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Update the state file with hashes for multiple artifacts.

    Args:
        artifact_paths: List of paths to artifact files.
        state_path: Optional path to the state file.
        descriptions: Optional dictionary mapping relative paths to descriptions.

    Returns:
        The updated state dictionary.
    """
    state = load_state(state_path)
    if "artifacts" not in state:
        state["artifacts"] = {}

    if descriptions is None:
        descriptions = {}

    for path in artifact_paths:
        rel_path = str(path.relative_to(PROJECT_ROOT))
        if not path.exists():
            raise FileNotFoundError(f"Artifact file not found: {path}")

        file_hash = compute_sha256(path)
        state["artifacts"][rel_path] = {
            "hash": file_hash,
            "updated_at": datetime.now().isoformat(),
            "description": descriptions.get(rel_path, f"Auto-generated hash for {rel_path}")
        }

    save_state(state, state_path)
    return state


def verify_artifact(
    artifact_path: Path,
    expected_hash: str,
    state_path: Optional[Path] = None
) -> bool:
    """
    Verify that an artifact's current hash matches the expected hash in the state file.

    Args:
        artifact_path: Path to the artifact file.
        expected_hash: The expected SHA-256 hash.
        state_path: Optional path to the state file.

    Returns:
        True if the hash matches, False otherwise.
    """
    if not artifact_path.exists():
        return False

    current_hash = compute_sha256(artifact_path)
    return current_hash == expected_hash


def main():
    """
    CLI entry point for state_manager.
    Usage: python -m code.utils.state_manager <update|verify> <file_path> [expected_hash]
    """
    if len(sys.argv) < 3:
        print("Usage: python -m code.utils.state_manager <update|verify> <file_path> [expected_hash]")
        sys.exit(1)

    command = sys.argv[1]
    file_path_str = sys.argv[2]
    file_path = PROJECT_ROOT / file_path_str

    if command == "update":
        try:
            state = update_artifact_state(file_path)
            print(f"Updated state for {file_path}")
            print(f"Hash: {state['artifacts'][str(file_path.relative_to(PROJECT_ROOT))]['hash']}")
        except Exception as e:
            print(f"Error updating state: {e}", file=sys.stderr)
            sys.exit(1)
    elif command == "verify":
        if len(sys.argv) < 4:
            print("Usage: python -m code.utils.state_manager verify <file_path> <expected_hash>")
            sys.exit(1)
        expected_hash = sys.argv[3]
        is_valid = verify_artifact(file_path, expected_hash)
        if is_valid:
            print(f"Verification successful for {file_path}")
            sys.exit(0)
        else:
            print(f"Verification failed for {file_path}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
