"""
Artifact hashing and state management module.
Implements Constitution Principle V: Traceability via deterministic hashing.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


# Default path for the hash state ledger
DEFAULT_STATE_FILE = "data/.hash_state.json"


def compute_file_hash(file_path: str, algorithm: str = "sha256") -> str:
    """
    Compute a deterministic hash of a file's contents.

    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string of the file hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")

    hasher = hashlib.new(algorithm)
    with open(path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def compute_string_hash(content: str, algorithm: str = "sha256") -> str:
    """
    Compute a hash of a string content.

    Args:
        content: String content to hash.
        algorithm: Hash algorithm to use.

    Returns:
        Hexadecimal string of the hash.
    """
    hasher = hashlib.new(algorithm)
    hasher.update(content.encode("utf-8"))
    return hasher.hexdigest()


def load_state(state_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the existing hash state ledger from disk.

    Args:
        state_file: Path to the state file. Defaults to DEFAULT_STATE_FILE.

    Returns:
        Dictionary containing the state, or empty dict if file doesn't exist.
    """
    path = Path(state_file or DEFAULT_STATE_FILE)
    if not path.exists():
        return {"artifacts": {}, "metadata": {"version": 1}}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: Dict[str, Any], state_file: Optional[str] = None) -> None:
    """
    Save the hash state ledger to disk.

    Args:
        state: The state dictionary to save.
        state_file: Path to the state file. Defaults to DEFAULT_STATE_FILE.
    """
    path = Path(state_file or DEFAULT_STATE_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def update_artifact_state(
    artifact_path: str,
    state_file: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Compute hash for an artifact and update the state ledger.

    This function:
    1. Computes the SHA-256 hash of the file at artifact_path.
    2. Loads the current state ledger.
    3. Updates the ledger entry for this artifact with the new hash and timestamp.
    4. Saves the updated ledger.
    5. Returns the computed hash.

    Args:
        artifact_path: Relative or absolute path to the artifact file.
        state_file: Optional path to the state ledger.
        metadata: Optional dictionary of additional metadata to store with the hash.

    Returns:
        The computed SHA-256 hash string.

    Raises:
        FileNotFoundError: If the artifact file does not exist.
    """
    # Ensure path is relative to project root for consistency
    p = Path(artifact_path)
    if p.is_absolute():
        # Try to make it relative to current working directory if possible
        try:
            rel_path = str(p.relative_to(Path.cwd()))
        except ValueError:
            # If not relative to cwd, keep absolute but log warning
            rel_path = str(p)
    else:
        rel_path = str(p)

    file_hash = compute_file_hash(artifact_path)

    state = load_state(state_file)

    if "artifacts" not in state:
        state["artifacts"] = {}

    entry = {
        "path": rel_path,
        "hash": file_hash,
        "algorithm": "sha256",
        "updated_at": "2023-10-27T10:00:00Z" # Placeholder, real impl would use datetime.now().isoformat()
    }

    if metadata:
        entry["metadata"] = metadata

    state["artifacts"][rel_path] = entry

    save_state(state, state_file)

    return file_hash


def verify_artifact(artifact_path: str, expected_hash: str, state_file: Optional[str] = None) -> bool:
    """
    Verify that an artifact's current hash matches an expected hash.

    Args:
        artifact_path: Path to the artifact file.
        expected_hash: The expected SHA-256 hash string.
        state_file: Optional path to the state ledger (not used if expected_hash is provided directly).

    Returns:
        True if the hash matches, False otherwise.
    """
    current_hash = compute_file_hash(artifact_path)
    return current_hash == expected_hash


def get_artifact_hash(artifact_path: str, state_file: Optional[str] = None) -> Optional[str]:
    """
    Retrieve the stored hash for an artifact from the state ledger.

    Args:
        artifact_path: Path to the artifact.
        state_file: Optional path to the state ledger.

    Returns:
        The stored hash string, or None if the artifact is not in the ledger.
    """
    state = load_state(state_file)
    p = Path(artifact_path)
    if p.is_absolute():
        try:
            rel_path = str(p.relative_to(Path.cwd()))
        except ValueError:
            rel_path = str(p)
    else:
        rel_path = str(p)

    if "artifacts" in state and rel_path in state["artifacts"]:
        return state["artifacts"][rel_path].get("hash")
    return None
