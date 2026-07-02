"""
State management module for artifact hashing and version tracking.

This module provides functionality to manage the `state.yaml` file, which tracks
the version and checksums of all significant artifacts produced by the pipeline.
This ensures reproducibility and allows for incremental execution.
"""
import os
import hashlib
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from config import PROJECT_ROOT, DATA_PROCESSED_DIR, DATA_GENERATED_DIR, DATA_RAW_DIR


STATE_FILE_PATH = PROJECT_ROOT / "state.yaml"


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def load_state() -> Dict[str, Any]:
    """
    Load the current state from state.yaml.
    
    Returns:
        Dictionary containing the state data. Returns an empty structure if file
        does not exist.
    """
    if not STATE_FILE_PATH.exists():
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "artifacts": {}
        }
    
    with open(STATE_FILE_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "artifacts": {}
        }


def save_state(state: Dict[str, Any]) -> None:
    """
    Save the state to state.yaml.
    
    Args:
        state: Dictionary containing the state data to save.
    """
    state["updated_at"] = datetime.now().isoformat()
    
    with open(STATE_FILE_PATH, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def register_artifact(
    artifact_path: Path, 
    artifact_type: str, 
    description: Optional[str] = None,
    source_task_id: Optional[str] = None
) -> None:
    """
    Register an artifact in the state file with its hash and metadata.
    
    Args:
        artifact_path: Path to the artifact file.
        artifact_type: Type of artifact (e.g., 'dataset', 'model', 'report', 'config').
        description: Optional description of the artifact.
        source_task_id: Optional ID of the task that generated this artifact.
        
    Raises:
        FileNotFoundError: If the artifact file does not exist.
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Cannot register non-existent artifact: {artifact_path}")
    
    state = load_state()
    
    # Ensure artifacts key exists
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    # Calculate relative path for storage
    try:
        relative_path = str(artifact_path.relative_to(PROJECT_ROOT))
    except ValueError:
        relative_path = str(artifact_path)
    
    artifact_info = {
        "path": relative_path,
        "type": artifact_type,
        "hash": calculate_file_hash(artifact_path),
        "size_bytes": artifact_path.stat().st_size,
        "created_at": datetime.fromtimestamp(artifact_path.stat().st_ctime).isoformat(),
        "description": description or "",
        "source_task_id": source_task_id or ""
    }
    
    state["artifacts"][relative_path] = artifact_info
    save_state(state)


def verify_artifact(artifact_path: Path) -> bool:
    """
    Verify the integrity of an artifact by comparing its hash with the stored state.
    
    Args:
        artifact_path: Path to the artifact file.
        
    Returns:
        True if the artifact exists and its hash matches the stored hash, False otherwise.
    """
    if not artifact_path.exists():
        return False
    
    state = load_state()
    
    try:
        relative_path = str(artifact_path.relative_to(PROJECT_ROOT))
    except ValueError:
        relative_path = str(artifact_path)
    
    if relative_path not in state.get("artifacts", {}):
        return False
    
    stored_hash = state["artifacts"][relative_path].get("hash")
    if not stored_hash:
        return False
    
    current_hash = calculate_file_hash(artifact_path)
    return current_hash == stored_hash


def initialize_state_file() -> None:
    """
    Initialize the state.yaml file if it does not exist.
    
    This creates the skeleton structure with versioning and empty artifacts dictionary.
    """
    if not STATE_FILE_PATH.exists():
        state = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "artifacts": {}
        }
        save_state(state)


def list_registered_artifacts() -> Dict[str, Dict[str, Any]]:
    """
    List all registered artifacts in the state file.
    
    Returns:
        Dictionary mapping artifact paths to their metadata.
    """
    state = load_state()
    return state.get("artifacts", {})