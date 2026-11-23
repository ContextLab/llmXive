"""
Versioning utilities for llmXive.

Provides functionality to compute SHA256 hashes for artifacts
and update project state YAML files.
"""
import hashlib
import os
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import yaml

from src.utils.config import get_project_root, get_state_path


def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute the SHA256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal SHA256 hash string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IsADirectoryError: If the path points to a directory.
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if file_path.is_dir():
        raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")
        
    sha256_hash = hashlib.sha256()
    
    # Read in chunks to handle large files without excessive memory usage
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
            
    return sha256_hash.hexdigest()


def compute_directory_hash(directory_path: Union[str, Path]) -> str:
    """
    Compute a deterministic hash for a directory based on its contents.
    
    This function recursively hashes all files in the directory and combines
    their hashes. Empty directories are ignored.
    
    Args:
        directory_path: Path to the directory.
        
    Returns:
        Hexadecimal SHA256 hash string representing the directory state.
        
    Raises:
        NotADirectoryError: If the path is not a directory.
    """
    directory_path = Path(directory_path)
    
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")
    if not directory_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory_path}")
        
    # Collect all files and sort them for deterministic ordering
    files = sorted(directory_path.rglob("*"))
    files = [f for f in files if f.is_file()]
    
    if not files:
        # Empty directory has a known hash
        return hashlib.sha256(b"empty_directory").hexdigest()
        
    combined_hash = hashlib.sha256()
    
    for file_path in files:
        # Include relative path in the hash to detect renames
        relative_path = file_path.relative_to(directory_path)
        combined_hash.update(str(relative_path).encode("utf-8"))
        
        # Hash file contents
        file_hash = compute_sha256(file_path)
        combined_hash.update(file_hash.encode("utf-8"))
        
    return combined_hash.hexdigest()


def update_state_file(
    project_id: str,
    artifact_path: Union[str, Path],
    state_key: str = "artifacts",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Update the project state YAML file with artifact versioning information.
    
    Args:
        project_id: The project identifier (e.g., 'PROJ-887-llmxive-follow-up-extending-latentskill').
        artifact_path: Path to the artifact to be recorded.
        state_key: The key under which to store artifact data (default: 'artifacts').
        metadata: Optional additional metadata to include in the state entry.
        
    Returns:
        The updated state dictionary.
        
    Raises:
        FileNotFoundError: If the state file's parent directory doesn't exist.
        ValueError: If the artifact path doesn't exist.
    """
    artifact_path = Path(artifact_path)
    
    if not artifact_path.exists():
        raise ValueError(f"Artifact does not exist: {artifact_path}")
        
    state_dir = get_state_path()
    state_dir.mkdir(parents=True, exist_ok=True)
    
    state_file = state_dir / f"{project_id}.yaml"
    
    # Load existing state or create new
    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {
            "project_id": project_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": None,
            state_key: {}
        }
        
    # Compute hash
    file_hash = compute_sha256(artifact_path)
    
    # Prepare artifact entry
    artifact_entry = {
        "path": str(artifact_path),
        "sha256": file_hash,
        "size_bytes": artifact_path.stat().st_size,
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    # Add any additional metadata
    if metadata:
        artifact_entry.update(metadata)
        
    # Update state
    if state_key not in state:
        state[state_key] = {}
        
    # Use relative path as key for easier lookup
    relative_path = str(artifact_path)
    state[state_key][relative_path] = artifact_entry
    state["updated_at"] = datetime.utcnow().isoformat()
    
    # Write updated state
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        
    return state


def verify_artifact(
    artifact_path: Union[str, Path],
    expected_hash: str
) -> bool:
    """
    Verify that an artifact's hash matches the expected value.
    
    Args:
        artifact_path: Path to the artifact.
        expected_hash: Expected SHA256 hash.
        
    Returns:
        True if hashes match, False otherwise.
        
    Raises:
        FileNotFoundError: If the artifact doesn't exist.
    """
    actual_hash = compute_sha256(artifact_path)
    return actual_hash == expected_hash


def get_artifact_state(
    project_id: str,
    artifact_path: Optional[Union[str, Path]] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieve state information for an artifact from the project state file.
    
    Args:
        project_id: The project identifier.
        artifact_path: Optional specific artifact path to look up.
                      If None, returns all artifact states.
                      
    Returns:
        Dictionary containing artifact state, or None if not found.
    """
    state_file = get_state_path() / f"{project_id}.yaml"
    
    if not state_file.exists():
        return None
        
    with open(state_file, "r", encoding="utf-8") as f:
        state = yaml.safe_load(f)
        
    if not state or "artifacts" not in state:
        return None
        
    if artifact_path is None:
        return state.get("artifacts", {})
        
    artifact_path_str = str(artifact_path)
    return state["artifacts"].get(artifact_path_str)


def batch_compute_hashes(
    artifact_paths: List[Union[str, Path]]
) -> Dict[str, str]:
    """
    Compute SHA256 hashes for multiple artifacts.
    
    Args:
        artifact_paths: List of artifact paths.
        
    Returns:
        Dictionary mapping artifact paths to their SHA256 hashes.
        
    Raises:
        FileNotFoundError: If any artifact doesn't exist.
    """
    results = {}
    for path in artifact_paths:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Artifact not found: {path}")
        results[str(path)] = compute_sha256(path)
    return results
