"""
State management for derived artifacts.

Computes SHA-256 hashes for files and updates the project state YAML.
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import yaml


def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_state(state_path: Path) -> Dict[str, Any]:
    """Load the current state YAML file, or return an empty structure if missing."""
    if not state_path.exists():
        return {
            "artifacts": {},
            "last_updated": None
        }
    with open(state_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"artifacts": {}, "last_updated": None}


def save_state(state_path: Path, state: Dict[str, Any]) -> None:
    """Save the state dictionary to the YAML file."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)


def update_artifact_state(
    state: Dict[str, Any],
    artifact_path: str,
    file_path: Path
) -> Dict[str, Any]:
    """
    Update the state dictionary with the hash and metadata for a single artifact.
    
    Args:
        state: The current state dictionary.
        artifact_path: The relative path string of the artifact (e.g., 'data/processed/descriptors.csv').
        file_path: The absolute Path to the file on disk.
    
    Returns:
        The updated state dictionary.
    """
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact file not found: {file_path}")
    
    file_hash = compute_sha256(file_path)
    file_size = file_path.stat().st_size
    
    state["artifacts"][artifact_path] = {
        "hash": file_hash,
        "size_bytes": file_size,
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
    
    state["last_updated"] = datetime.utcnow().isoformat() + "Z"
    return state


def verify_artifact(state: Dict[str, Any], artifact_path: str, file_path: Path) -> bool:
    """
    Verify that a file's hash matches the one stored in the state.
    
    Returns:
        True if the hash matches, False otherwise.
    """
    if "artifacts" not in state or artifact_path not in state["artifacts"]:
        return False
    
    stored_hash = state["artifacts"][artifact_path].get("hash")
    if not stored_hash:
        return False
    
    current_hash = compute_sha256(file_path)
    return stored_hash == current_hash


def update_state_for_multiple_artifacts(
    state_path: Path,
    artifacts: List[Dict[str, str]]
) -> None:
    """
    Load state, update hashes for multiple artifacts, and save back.
    
    Args:
        state_path: Path to the state YAML file.
        artifacts: List of dicts with keys 'relative_path' (str) and 'absolute_path' (str).
    """
    state = load_state(state_path)
    
    for item in artifacts:
        rel_path = item["relative_path"]
        abs_path = Path(item["absolute_path"])
        state = update_artifact_state(state, rel_path, abs_path)
    
    save_state(state_path, state)
