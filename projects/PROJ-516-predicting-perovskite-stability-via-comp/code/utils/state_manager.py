"""
State Manager for llmXive pipeline.
Computes SHA-256 hashes for derived artifacts and updates the project state file.
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import yaml

# Path to the state file relative to project root
STATE_FILE_PATH = Path("state/pipeline_state.yaml")

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
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")

def load_state() -> Dict[str, Any]:
    """
    Load the current pipeline state from the YAML file.

    Returns:
        Dictionary containing the pipeline state. Returns an empty dict
        if the file does not exist.
    """
    if not STATE_FILE_PATH.exists():
        return {"artifacts": {}, "last_updated": None, "version": "1.0"}

    try:
        with open(STATE_FILE_PATH, "r") as f:
            state = yaml.safe_load(f)
            return state if state else {"artifacts": {}, "last_updated": None, "version": "1.0"}
    except yaml.YAMLError as e:
        # If YAML is corrupted, reset state to avoid crashes
        print(f"Warning: Could not parse state file, resetting state. Error: {e}")
        return {"artifacts": {}, "last_updated": None, "version": "1.0"}

def save_state(state: Dict[str, Any]) -> None:
    """
    Save the pipeline state to the YAML file.

    Args:
        state: Dictionary containing the pipeline state.
    """
    # Ensure state directory exists
    STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(STATE_FILE_PATH, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def update_artifact_state(
    artifact_path: Path,
    state: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Compute the hash for a specific artifact and update the state dictionary.

    Args:
        artifact_path: Path to the artifact file.
        state: Optional existing state dictionary. If None, loads from disk.

    Returns:
        Updated state dictionary.
    """
    if state is None:
        state = load_state()

    if not state.get("artifacts"):
        state["artifacts"] = {}

    # Normalize path to string key relative to project root
    # Ensure we handle both absolute and relative paths correctly
    try:
        # If it's an absolute path, try to make it relative to cwd
        if artifact_path.is_absolute():
            try:
                key = str(artifact_path.relative_to(Path.cwd()))
            except ValueError:
                # If not relative to cwd, use absolute path string
                key = str(artifact_path)
        else:
            key = str(artifact_path)
    except Exception:
        key = str(artifact_path)

    file_hash = compute_sha256(artifact_path)

    state["artifacts"][key] = {
        "hash": file_hash,
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }

    state["last_updated"] = datetime.utcnow().isoformat() + "Z"

    return state

def update_state_for_multiple_artifacts(
    artifact_paths: List[Path]
) -> Dict[str, Any]:
    """
    Update the state for multiple artifacts at once.

    Args:
        artifact_paths: List of paths to artifact files.

    Returns:
        Updated state dictionary.
    """
    state = load_state()
    for path in artifact_paths:
        if path.exists():
            state = update_artifact_state(path, state)
        else:
            # Log warning but do not fail if file is missing
            # This allows partial state updates
            print(f"Warning: Artifact not found for state update: {path}")

    save_state(state)
    return state

def verify_artifact(artifact_path: Path, expected_hash: Optional[str] = None) -> bool:
    """
    Verify the hash of an artifact against the stored state or an expected value.

    Args:
        artifact_path: Path to the artifact file.
        expected_hash: Optional specific hash to verify against.
                       If None, compares against the stored state.

    Returns:
        True if the artifact hash matches the expected/stored hash, False otherwise.
    """
    if not artifact_path.exists():
        return False

    current_hash = compute_sha256(artifact_path)

    if expected_hash:
        return current_hash == expected_hash

    state = load_state()
    # Normalize path key
    try:
        if artifact_path.is_absolute():
            try:
                key = str(artifact_path.relative_to(Path.cwd()))
            except ValueError:
                key = str(artifact_path)
        else:
            key = str(artifact_path)
    except Exception:
        key = str(artifact_path)

    if key not in state.get("artifacts", {}):
        return False

    stored_hash = state["artifacts"][key].get("hash")
    return current_hash == stored_hash

def main():
    """
    CLI entry point for state management operations.
    Usage:
      python -m code.utils.state_manager update <path>
      python -m code.utils.state_manager verify <path>
    """
    import sys
    if len(sys.argv) < 3:
        print("Usage: python -m code.utils.state_manager <update|verify> <file_path>")
        sys.exit(1)

    command = sys.argv[1]
    file_path = Path(sys.argv[2])

    if command == "update":
        state = update_artifact_state(file_path)
        save_state(state)
        print(f"Updated state for: {file_path}")
    elif command == "verify":
        is_valid = verify_artifact(file_path)
        if is_valid:
            print(f"Verification passed for: {file_path}")
        else:
            print(f"Verification FAILED for: {file_path}")
        sys.exit(0 if is_valid else 1)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()