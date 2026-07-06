"""
State management module for tracking artifact hashes and project state.

This module provides functionality to compute SHA-256 hashes for derived artifacts
and maintain a persistent state file (state/...yaml) that tracks the current
version of all project artifacts.
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
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()


def load_state(state_path: Path) -> Dict[str, Any]:
    """
    Load the current state from a YAML file.
    
    Args:
        state_path: Path to the state YAML file.
        
    Returns:
        Dictionary containing the project state.
        
    Raises:
        FileNotFoundError: If the state file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
    """
    if not state_path.exists():
        # Return an empty state if the file doesn't exist
        return {
            "version": "1.0",
            "last_updated": None,
            "artifacts": {}
        }
    
    with open(state_path, "r") as f:
        state = yaml.safe_load(f)
    
    if state is None:
        return {
            "version": "1.0",
            "last_updated": None,
            "artifacts": {}
        }
    
    return state


def save_state(state: Dict[str, Any], state_path: Path) -> None:
    """
    Save the project state to a YAML file.
    
    Args:
        state: Dictionary containing the project state.
        state_path: Path to the state YAML file.
    """
    # Ensure the directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)


def update_artifact_state(
    state: Dict[str, Any],
    artifact_path: Path,
    artifact_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update the state entry for a single artifact.
    
    Args:
        state: Current project state dictionary.
        artifact_path: Path to the artifact file.
        artifact_name: Optional name for the artifact. If not provided,
                      the relative path is used.
                      
    Returns:
        Updated state dictionary.
        
    Raises:
        FileNotFoundError: If the artifact file does not exist.
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
    
    if artifact_name is None:
        artifact_name = str(artifact_path.relative_to(Path.cwd()))
    
    # Compute hash
    file_hash = compute_sha256(artifact_path)
    
    # Get file metadata
    stat = artifact_path.stat()
    
    # Update state
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    state["artifacts"][artifact_name] = {
        "hash": file_hash,
        "path": str(artifact_path),
        "size_bytes": stat.st_size,
        "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    state["last_updated"] = datetime.now().isoformat()
    
    return state


def verify_artifact(
    artifact_path: Path,
    state: Dict[str, Any],
    artifact_name: Optional[str] = None
) -> bool:
    """
    Verify that an artifact's current hash matches the stored hash in state.
    
    Args:
        artifact_path: Path to the artifact file.
        state: Current project state dictionary.
        artifact_name: Optional name for the artifact. If not provided,
                      the relative path is used.
                      
    Returns:
        True if the artifact hash matches the stored hash, False otherwise.
        
    Raises:
        FileNotFoundError: If the artifact file does not exist.
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
    
    if artifact_name is None:
        artifact_name = str(artifact_path.relative_to(Path.cwd()))
    
    if "artifacts" not in state or artifact_name not in state["artifacts"]:
        return False
    
    stored_hash = state["artifacts"][artifact_name].get("hash")
    if stored_hash is None:
        return False
    
    current_hash = compute_sha256(artifact_path)
    
    return current_hash == stored_hash


def update_state_for_multiple_artifacts(
    state_path: Path,
    artifact_paths: List[Path],
    artifact_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Update the state file for multiple artifacts at once.
    
    Args:
        state_path: Path to the state YAML file.
        artifact_paths: List of paths to artifact files.
        artifact_names: Optional list of names for the artifacts. If not provided,
                       the relative paths are used.
                       
    Returns:
        Updated state dictionary.
        
    Raises:
        FileNotFoundError: If any artifact file does not exist.
    """
    # Load current state
    state = load_state(state_path)
    
    # Update for each artifact
    for i, artifact_path in enumerate(artifact_paths):
        name = None
        if artifact_names is not None and i < len(artifact_names):
            name = artifact_names[i]
        
        state = update_artifact_state(state, artifact_path, name)
    
    # Save updated state
    save_state(state, state_path)
    
    return state