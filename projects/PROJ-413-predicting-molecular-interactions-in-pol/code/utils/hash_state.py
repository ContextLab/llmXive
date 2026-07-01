"""
Utilities for computing SHA256 hashes and managing project state YAML.

This module provides functions to compute file hashes, hash directories,
update the central project state file, and verify artifact integrity.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA256 hash.
    
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def hash_directory(dir_path: Path, pattern: str = "*") -> Dict[str, str]:
    """
    Compute SHA256 hashes for all files in a directory matching a pattern.

    Args:
        dir_path: Path to the directory.
        pattern: Glob pattern for files (default: "*").

    Returns:
        Dictionary mapping relative file paths to their hashes.
    """
    hashes = {}
    for file_path in dir_path.glob(pattern):
        if file_path.is_file():
            rel_path = file_path.relative_to(dir_path)
            hashes[str(rel_path)] = compute_sha256(file_path)
    return hashes

def update_state_yaml(state_path: Path, artifact_name: str, artifact_hash: str) -> None:
    """
    Update or create a project state YAML file with a new artifact hash.

    Args:
        state_path: Path to the state YAML file.
        artifact_name: Name of the artifact (e.g., 'curated_dataset.csv').
        artifact_hash: SHA256 hash of the artifact.
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    if state_path.exists():
        with open(state_path, 'r') as f:
            try:
                state_data = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                state_data = {}
    else:
        state_data = {"artifacts": {}}

    if "artifacts" not in state_data:
        state_data["artifacts"] = {}

    state_data["artifacts"][artifact_name] = artifact_hash

    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)

def verify_artifacts(state_path: Path, base_dir: Path) -> Dict[str, bool]:
    """
    Verify the integrity of artifacts listed in the state file.

    Args:
        state_path: Path to the state YAML file.
        base_dir: Base directory where artifacts are located.

    Returns:
        Dictionary mapping artifact names to verification status (True/False).
    """
    if not state_path.exists():
        return {}

    with open(state_path, 'r') as f:
        state_data = yaml.safe_load(f)

    results = {}
    artifacts = state_data.get("artifacts", {})

    for artifact_name, expected_hash in artifacts.items():
        file_path = base_dir / artifact_name
        if not file_path.exists():
            results[artifact_name] = False
            continue

        try:
            actual_hash = compute_sha256(file_path)
            results[artifact_name] = (actual_hash == expected_hash)
        except Exception:
            results[artifact_name] = False

    return results

def get_state_hash(state_path: Path) -> Optional[str]:
    """
    Compute the SHA256 hash of the state file itself.

    Args:
        state_path: Path to the state YAML file.

    Returns:
        Hexadecimal string of the state file's hash, or None if file doesn't exist.
    """
    if not state_path.exists():
        return None
    return compute_sha256(state_path)
