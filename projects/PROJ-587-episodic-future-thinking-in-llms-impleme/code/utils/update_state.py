"""
Artifact State Management for Constitution Principle V.

This module manages artifact hashes and timestamps to ensure reproducibility
and traceability of all generated artifacts in the research pipeline.
"""

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Project root relative to this file's location
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = PROJECT_ROOT / "data" / "artifact_state.json"


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file's contents.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if file_path.is_dir():
        raise IsADirectoryError(f"Path is a directory: {file_path}")

    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_state() -> Dict[str, Any]:
    """
    Load the artifact state from the state file.

    Returns:
        Dictionary containing artifact metadata. Returns an empty structure
        if the file does not exist.
    """
    if not STATE_FILE.exists():
        return {
            "artifacts": {},
            "last_updated": None,
            "version": "1.0"
        }

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: Dict[str, Any]) -> None:
    """
    Save the artifact state to the state file.

    Args:
        state: Dictionary containing artifact metadata to save.
    """
    # Ensure directory exists
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Add metadata
    state["last_updated"] = datetime.utcnow().isoformat() + "Z"

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def update_artifact(
    artifact_path: Path,
    artifact_type: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Tuple[str, str]:
    """
    Update the state record for a specific artifact.

    This function:
    1. Computes the SHA-256 hash of the artifact file.
    2. Records the file size and modification time.
    3. Stores custom metadata if provided.
    4. Persists the updated state.

    Args:
        artifact_path: Path to the artifact file.
        artifact_type: Category of artifact (e.g., 'script', 'data', 'model').
        metadata: Optional dictionary of additional metadata to store.

    Returns:
        Tuple of (artifact_path_str, hash).

    Raises:
        FileNotFoundError: If the artifact file does not exist.
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")

    # Compute hash
    file_hash = compute_file_hash(artifact_path)

    # Get file stats
    stat = artifact_path.stat()
    file_size = stat.st_size
    modified_time = datetime.fromtimestamp(stat.st_mtime).isoformat() + "Z"

    # Load current state
    state = load_state()

    # Create artifact key (relative path from project root)
    try:
        relative_path = artifact_path.relative_to(PROJECT_ROOT)
    except ValueError:
        # If not under project root, use absolute path string
        relative_path = artifact_path

    artifact_key = str(relative_path)

    # Build artifact record
    record = {
        "path": artifact_key,
        "type": artifact_type,
        "hash": file_hash,
        "size_bytes": file_size,
        "modified_at": modified_time,
        "created_at": state["artifacts"].get(artifact_key, {}).get("created_at", modified_time)
    }

    # Add custom metadata
    if metadata:
        record["metadata"] = metadata

    # Update state
    state["artifacts"][artifact_key] = record

    # Save state
    save_state(state)

    return artifact_key, file_hash


def verify_artifact(artifact_path: Path) -> bool:
    """
    Verify an artifact's hash against the recorded state.

    Args:
        artifact_path: Path to the artifact file.

    Returns:
        True if the artifact exists and its hash matches the recorded hash.
        False otherwise.
    """
    if not artifact_path.exists():
        return False

    try:
        relative_path = artifact_path.relative_to(PROJECT_ROOT)
    except ValueError:
        relative_path = artifact_path

    state = load_state()
    artifact_key = str(relative_path)

    if artifact_key not in state["artifacts"]:
        return False

    recorded_hash = state["artifacts"][artifact_key]["hash"]
    current_hash = compute_file_hash(artifact_path)

    return recorded_hash == current_hash


def get_artifact_info(artifact_path: Path) -> Optional[Dict[str, Any]]:
    """
    Retrieve recorded information for an artifact.

    Args:
        artifact_path: Path to the artifact file.

    Returns:
        Dictionary of artifact metadata, or None if not found.
    """
    try:
        relative_path = artifact_path.relative_to(PROJECT_ROOT)
    except ValueError:
        relative_path = artifact_path

    state = load_state()
    artifact_key = str(relative_path)

    return state["artifacts"].get(artifact_key)


def list_artifacts(artifact_type: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    List all registered artifacts, optionally filtered by type.

    Args:
        artifact_type: Optional filter for artifact type.

    Returns:
        Dictionary mapping artifact paths to their metadata.
    """
    state = load_state()
    artifacts = state["artifacts"]

    if artifact_type:
        return {
            k: v for k, v in artifacts.items()
            if v.get("type") == artifact_type
        }

    return artifacts


def main() -> None:
    """
    CLI entry point for artifact state management.

    Usage:
        python utils/update_state.py register <path> <type> [metadata_json]
        python utils/update_state.py verify <path>
        python utils/update_state.py info <path>
        python utils/update_state.py list [type]
    """
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python utils/update_state.py register <path> <type> [metadata_json]")
        print("  python utils/update_state.py verify <path>")
        print("  python utils/update_state.py info <path>")
        print("  python utils/update_state.py list [type]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "register":
        if len(sys.argv) < 4:
            print("Error: register requires <path> and <type>")
            sys.exit(1)

        path_str = sys.argv[2]
        artifact_type = sys.argv[3]
        metadata = json.loads(sys.argv[4]) if len(sys.argv) > 4 else None

        artifact_path = Path(path_str)
        if not artifact_path.is_absolute():
            artifact_path = PROJECT_ROOT / artifact_path

        try:
            key, hash_val = update_artifact(artifact_path, artifact_type, metadata)
            print(f"Registered: {key}")
            print(f"Hash: {hash_val}")
        except (FileNotFoundError, IsADirectoryError, json.JSONDecodeError) as e:
            print(f"Error: {e}")
            sys.exit(1)

    elif command == "verify":
        if len(sys.argv) < 3:
            print("Error: verify requires <path>")
            sys.exit(1)

        path_str = sys.argv[2]
        artifact_path = Path(path_str)
        if not artifact_path.is_absolute():
            artifact_path = PROJECT_ROOT / artifact_path

        if verify_artifact(artifact_path):
            print(f"Verified: {artifact_path}")
        else:
            print(f"Verification failed: {artifact_path}")
            sys.exit(1)

    elif command == "info":
        if len(sys.argv) < 3:
            print("Error: info requires <path>")
            sys.exit(1)

        path_str = sys.argv[2]
        artifact_path = Path(path_str)
        if not artifact_path.is_absolute():
            artifact_path = PROJECT_ROOT / artifact_path

        info = get_artifact_info(artifact_path)
        if info:
            print(json.dumps(info, indent=2))
        else:
            print(f"No info found for: {artifact_path}")
            sys.exit(1)

    elif command == "list":
        artifact_type = sys.argv[2] if len(sys.argv) > 2 else None
        artifacts = list_artifacts(artifact_type)
        if artifacts:
            print(json.dumps(artifacts, indent=2))
        else:
            print("No artifacts found.")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
