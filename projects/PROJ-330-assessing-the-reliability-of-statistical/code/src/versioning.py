"""
Versioning Module for Artifact State Management.

This module provides functions to compute SHA256 hashes of artifacts,
load and save state files, and update artifact state with hashes.
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from src.config import ensure_directories, PROJECT_ROOT, STATE_FILE

def compute_sha256(file_path: str) -> str:
    """
    Compute SHA256 hash of a file.

    Args:
        file_path: Path to the file to hash

    Returns:
        str: Hexadecimal SHA256 hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state() -> Dict[str, Any]:
    """
    Load the project state file.

    Returns:
        dict: State dictionary containing artifact information
    """
    ensure_directories()

    if not STATE_FILE.exists():
        return {
            "artifacts": {},
            "last_updated": None
        }

    with open(STATE_FILE, 'r') as f:
        state = yaml.safe_load(f)

    return state if state else {"artifacts": {}, "last_updated": None}

def save_state(state: Dict[str, Any]) -> None:
    """
    Save the project state file.

    Args:
        state: State dictionary to save
    """
    ensure_directories()

    import datetime
    state["last_updated"] = datetime.datetime.now().isoformat()

    with open(STATE_FILE, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)

def update_artifact_state(state: Dict[str, Any], artifact_path: str, hash_value: str) -> None:
    """
    Update the state dictionary with a new artifact hash.

    This function adds or updates an artifact entry in the state dictionary
    with its path and SHA256 hash.

    Args:
        state: State dictionary to update (modified in place)
        artifact_path: Relative path to the artifact from project root
        hash_value: SHA256 hash of the artifact
    """
    if "artifacts" not in state:
        state["artifacts"] = {}

    state["artifacts"][artifact_path] = {
        "hash": hash_value,
        "updated": __import__('datetime').datetime.now().isoformat()
    }

def verify_artifact(artifact_path: str, expected_hash: str) -> bool:
    """
    Verify that an artifact matches its expected hash.

    Args:
        artifact_path: Path to the artifact file
        expected_hash: Expected SHA256 hash

    Returns:
        bool: True if hash matches, False otherwise
    """
    full_path = PROJECT_ROOT / artifact_path

    if not full_path.exists():
        return False

    actual_hash = compute_sha256(str(full_path))
    return actual_hash == expected_hash