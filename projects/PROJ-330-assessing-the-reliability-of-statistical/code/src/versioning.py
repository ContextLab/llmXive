"""
Versioning module for llmXive pipeline.

Computes SHA256 hashes of artifacts and updates state.yaml to track
the provenance and integrity of generated files.
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, Any, Optional

import yaml

from src.config import ensure_directories, PROJECT_ROOT


def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def load_state(state_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the state.yaml file.

    Args:
        state_path: Optional path to the state file. Defaults to PROJECT_ROOT / 'state.yaml'.

    Returns:
        Dictionary representing the state file contents.
        Returns an empty dict with 'artifacts' key if file does not exist.
    """
    if state_path is None:
        state_path = PROJECT_ROOT / "state.yaml"

    if not state_path.exists():
        return {"artifacts": {}}

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data is None:
                return {"artifacts": {}}
            if "artifacts" not in data:
                data["artifacts"] = {}
            return data
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in state file {state_path}: {e}")


def save_state(state: Dict[str, Any], state_path: Optional[Path] = None) -> None:
    """
    Save the state dictionary to state.yaml.

    Args:
        state: Dictionary to save.
        state_path: Optional path to the state file. Defaults to PROJECT_ROOT / 'state.yaml'.
    """
    if state_path is None:
        state_path = PROJECT_ROOT / "state.yaml"

    ensure_directories()
    with open(state_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(state, f, default_flow_style=False, sort_keys=False)


def update_artifact_state(
    artifact_path: Path,
    state_path: Optional[Path] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Compute the hash of an artifact and update the state.yaml file.

    Args:
        artifact_path: Path to the artifact file.
        state_path: Optional path to the state file. Defaults to PROJECT_ROOT / 'state.yaml'.
        metadata: Optional dictionary of additional metadata to store with the artifact entry.

    Returns:
        The updated state dictionary.

    Raises:
        FileNotFoundError: If the artifact does not exist.
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")

    state = load_state(state_path)

    # Use relative path from project root as the key
    try:
        relative_key = str(artifact_path.relative_to(PROJECT_ROOT))
    except ValueError:
        # If artifact is not under PROJECT_ROOT, use absolute path
        relative_key = str(artifact_path)

    hash_value = compute_sha256(artifact_path)

    entry = {
        "hash": hash_value,
        "path": relative_key,
        "size_bytes": artifact_path.stat().st_size
    }

    if metadata:
        entry.update(metadata)

    state["artifacts"][relative_key] = entry

    save_state(state, state_path)

    return state


def verify_artifact(artifact_path: Path, expected_hash: str, state_path: Optional[Path] = None) -> bool:
    """
    Verify the hash of an artifact against an expected value.

    Args:
        artifact_path: Path to the artifact file.
        expected_hash: Expected SHA256 hash string.
        state_path: Optional path to the state file.

    Returns:
        True if the hash matches, False otherwise.

    Raises:
        FileNotFoundError: If the artifact does not exist.
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")

    actual_hash = compute_sha256(artifact_path)
    return actual_hash == expected_hash
