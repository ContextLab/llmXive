"""
State Manager Module for llmXive Pipeline.

This module provides functionality to compute SHA-256 hashes for derived artifacts
and manage the project state in YAML files.
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import yaml


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


def load_state(state_path: Path) -> Dict[str, Any]:
    """
    Load the current state from a YAML file.

    Args:
        state_path: Path to the state YAML file.

    Returns:
        Dictionary containing the state. Returns an empty dict if file doesn't exist.
    """
    if not state_path.exists():
        return {"artifacts": {}, "metadata": {}}

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f)
            # Ensure structure exists
            if not isinstance(state, dict):
                return {"artifacts": {}, "metadata": {}}
            if "artifacts" not in state:
                state["artifacts"] = {}
            if "metadata" not in state:
                state["metadata"] = {}
            return state
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in state file {state_path}: {e}")


def save_state(state: Dict[str, Any], state_path: Path) -> None:
    """
    Save the state to a YAML file.

    Args:
        state: Dictionary containing the state.
        state_path: Path to the state YAML file.
    """
    # Ensure parent directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)


def update_artifact_state(
    artifact_path: Path, state: Dict[str, Any], state_path: Path
) -> Dict[str, Any]:
    """
    Update the state for a single artifact.

    Computes the SHA-256 hash of the artifact and updates the state dictionary.

    Args:
        artifact_path: Path to the artifact file.
        state: Current state dictionary.
        state_path: Path to the state file (for saving).

    Returns:
        Updated state dictionary.
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Cannot update state for missing artifact: {artifact_path}")

    relative_path = artifact_path.name
    if artifact_path.parent != state_path.parent:
        # Try to make it relative to the project root if possible
        try:
            relative_path = artifact_path.relative_to(state_path.parent.parent)
        except ValueError:
            relative_path = str(artifact_path)

    try:
        file_hash = compute_sha256(artifact_path)
    except (FileNotFoundError, IOError) as e:
        raise RuntimeError(f"Failed to compute hash for {artifact_path}: {e}")

    timestamp = datetime.utcnow().isoformat() + "Z"

    state["artifacts"][str(relative_path)] = {
        "hash": file_hash,
        "updated_at": timestamp,
        "size_bytes": artifact_path.stat().st_size,
    }

    # Update metadata
    state["metadata"]["last_updated"] = timestamp
    state["metadata"]["artifact_count"] = len(state["artifacts"])

    save_state(state, state_path)
    return state


def verify_artifact(artifact_path: Path, expected_hash: str) -> bool:
    """
    Verify an artifact against an expected hash.

    Args:
        artifact_path: Path to the artifact file.
        expected_hash: Expected SHA-256 hash.

    Returns:
        True if the artifact matches the expected hash, False otherwise.

    Raises:
        FileNotFoundError: If the artifact does not exist.
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")

    actual_hash = compute_sha256(artifact_path)
    return actual_hash == expected_hash


def update_state_for_multiple_artifacts(
    artifact_paths: List[Path], state_path: Path
) -> Dict[str, Any]:
    """
    Update the state for multiple artifacts at once.

    Args:
        artifact_paths: List of paths to artifact files.
        state_path: Path to the state YAML file.

    Returns:
        Updated state dictionary.

    Raises:
        FileNotFoundError: If any artifact does not exist.
    """
    state = load_state(state_path)
    missing = [p for p in artifact_paths if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing artifacts: {missing}")

    for artifact_path in artifact_paths:
        state = update_artifact_state(artifact_path, state, state_path)

    return state
