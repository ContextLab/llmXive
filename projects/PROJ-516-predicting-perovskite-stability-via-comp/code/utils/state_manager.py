"""
State Manager Module for llmXive Project PROJ-516.

This module provides functionality to compute SHA-256 hashes for derived artifacts
and update the project state file (state/...yaml) to track artifact integrity and versioning.
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
STATE_DIR = PROJECT_ROOT / "state"
STATE_FILE = STATE_DIR / "artifact_state.yaml"

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
    Load the current state from the state file.

    Returns:
        Dictionary containing the current state. Returns an empty dict if file doesn't exist.
    """
    if not STATE_FILE.exists():
        # Ensure state directory exists
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        return {
            "last_updated": None,
            "artifacts": {}
        }

    try:
        with open(STATE_FILE, "r") as f:
            return yaml.safe_load(f) or {"last_updated": None, "artifacts": {}}
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing state file {STATE_FILE}: {e}")

def save_state(state: Dict[str, Any]) -> None:
    """
    Save the state dictionary to the state file.

    Args:
        state: Dictionary containing the state to save.
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def update_artifact_state(artifact_path: Path, description: Optional[str] = None) -> None:
    """
    Compute the hash for a single artifact and update the state file.

    Args:
        artifact_path: Relative or absolute path to the artifact.
        description: Optional description of the artifact.
    """
    # Resolve to absolute path
    abs_path = artifact_path.resolve()

    # Verify file exists
    if not abs_path.exists():
        raise FileNotFoundError(f"Cannot update state for non-existent file: {abs_path}")

    # Compute hash
    file_hash = compute_sha256(abs_path)

    # Load current state
    state = load_state()

    # Determine relative path for storage
    try:
        rel_path = str(abs_path.relative_to(PROJECT_ROOT))
    except ValueError:
        # If not under project root, use absolute path string
        rel_path = str(abs_path)

    # Update state entry
    state["artifacts"][rel_path] = {
        "hash": file_hash,
        "size_bytes": abs_path.stat().st_size,
        "description": description or "No description provided",
        "last_updated": datetime.utcnow().isoformat()
    }

    # Update timestamp
    state["last_updated"] = datetime.utcnow().isoformat()

    # Save state
    save_state(state)

def update_state_for_multiple_artifacts(artifacts: List[Dict[str, Any]]) -> None:
    """
    Update state for multiple artifacts at once.

    Args:
        artifacts: List of dictionaries with keys:
                   - 'path': Path to the artifact (str or Path)
                   - 'description': Optional description (str)
    """
    state = load_state()

    for item in artifacts:
        path = item["path"]
        desc = item.get("description")

        abs_path = Path(path).resolve()

        if not abs_path.exists():
            print(f"Warning: Skipping non-existent file {abs_path}", file=sys.stderr)
            continue

        file_hash = compute_sha256(abs_path)

        try:
            rel_path = str(abs_path.relative_to(PROJECT_ROOT))
        except ValueError:
            rel_path = str(abs_path)

        state["artifacts"][rel_path] = {
            "hash": file_hash,
            "size_bytes": abs_path.stat().st_size,
            "description": desc or "No description provided",
            "last_updated": datetime.utcnow().isoformat()
        }

    state["last_updated"] = datetime.utcnow().isoformat()
    save_state(state)

def verify_artifact(artifact_path: Path) -> bool:
    """
    Verify an artifact's hash against the stored state.

    Args:
        artifact_path: Path to the artifact to verify.

    Returns:
        True if the hash matches, False otherwise.

    Raises:
        FileNotFoundError: If the artifact or state file is missing.
    """
    abs_path = artifact_path.resolve()

    if not abs_path.exists():
        raise FileNotFoundError(f"Artifact not found: {abs_path}")

    try:
        rel_path = str(abs_path.relative_to(PROJECT_ROOT))
    except ValueError:
        rel_path = str(abs_path)

    state = load_state()

    if rel_path not in state.get("artifacts", {}):
        raise FileNotFoundError(f"No state record found for: {rel_path}")

    stored_hash = state["artifacts"][rel_path]["hash"]
    current_hash = compute_sha256(abs_path)

    return stored_hash == current_hash

def main():
    """
    CLI entry point for state management operations.
    Usage: python -m code.utils.state_manager <update|verify> <file_path>
    """
    if len(sys.argv) < 3:
        print("Usage: python -m code.utils.state_manager <update|verify> <file_path>")
        sys.exit(1)

    operation = sys.argv[1].lower()
    file_path = Path(sys.argv[2])

    try:
        if operation == "update":
            update_artifact_state(file_path)
            print(f"State updated for: {file_path}")
        elif operation == "verify":
            if verify_artifact(file_path):
                print(f"Verification PASSED for: {file_path}")
                sys.exit(0)
            else:
                print(f"Verification FAILED for: {file_path} (Hash mismatch)")
                sys.exit(1)
        else:
            print(f"Unknown operation: {operation}")
            print("Usage: python -m code.utils.state_manager <update|verify> <file_path>")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()