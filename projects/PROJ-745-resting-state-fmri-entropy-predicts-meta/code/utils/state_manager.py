"""
State management utilities for the llmXive pipeline.

Implements Constitution Principle V: Automated state file updates.
Tracks artifact modifications and updates timestamps automatically.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

# Default state file path relative to project root
DEFAULT_STATE_FILE = "data/state.json"

def get_state_file_path(project_root: Optional[Path] = None) -> Path:
    """
    Determine the path to the state file.
    
    Args:
        project_root: Base directory for the project. Defaults to current working directory.
        
    Returns:
        Path object pointing to the state file.
    """
    if project_root is None:
        project_root = Path.cwd()
    return project_root / DEFAULT_STATE_FILE

def load_state(project_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the state file from disk.
    
    If the state file does not exist, returns an empty state dictionary.
    
    Args:
        project_root: Base directory for the project.
        
    Returns:
        Dictionary containing state data.
    """
    state_path = get_state_file_path(project_root)
    
    if not state_path.exists():
        logger.debug(f"State file not found at {state_path}. Initializing empty state.")
        return {
            "version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "artifacts": {}
        }
    
    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
        logger.info(f"Loaded state from {state_path}")
        return state
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load state file: {e}")
        # Return a fresh state on corruption
        return {
            "version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "artifacts": {}
        }

def save_state(state: Dict[str, Any], project_root: Optional[Path] = None) -> Path:
    """
    Save the state dictionary to disk.
    
    Ensures the parent directory exists before writing.
    
    Args:
        state: Dictionary containing state data.
        project_root: Base directory for the project.
        
    Returns:
        Path to the saved state file.
    """
    state_path = get_state_file_path(project_root)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, default=str)
    
    logger.info(f"Saved state to {state_path}")
    return state_path

def register_artifact(
    artifact_path: str,
    artifact_type: str,
    state: Optional[Dict[str, Any]] = None,
    project_root: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Register or update an artifact in the state file.
    
    Updates the 'updated_at' timestamp of the state file and the specific artifact
    entry, implementing Constitution Principle V.
    
    Args:
        artifact_path: Relative path to the artifact (e.g., 'data/processed/subject_001.csv').
        artifact_type: Type of artifact (e.g., 'csv', 'nifti', 'figure', 'model').
        state: Existing state dictionary. If None, loads from disk.
        project_root: Base directory for the project.
        
    Returns:
        Updated state dictionary.
    """
    if state is None:
        state = load_state(project_root)
    
    current_time = datetime.now(timezone.utc).isoformat()
    
    # Ensure artifacts key exists
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    # Normalize path to use forward slashes
    normalized_path = artifact_path.replace(os.sep, '/')
    
    # Register or update artifact entry
    state["artifacts"][normalized_path] = {
        "type": artifact_type,
        "registered_at": current_time,
        "updated_at": current_time,
        "path": normalized_path
    }
    
    # Update global updated_at timestamp (Constitution Principle V)
    state["updated_at"] = current_time
    
    # Save immediately to disk
    save_state(state, project_root)
    
    logger.info(f"Registered artifact: {normalized_path} (type: {artifact_type})")
    return state

def update_artifact_timestamp(
    artifact_path: str,
    state: Optional[Dict[str, Any]] = None,
    project_root: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Update the timestamp of an existing artifact.
    
    Called when an artifact is modified after initial registration.
    Updates the global 'updated_at' timestamp as per Constitution Principle V.
    
    Args:
        artifact_path: Relative path to the artifact.
        state: Existing state dictionary. If None, loads from disk.
        project_root: Base directory for the project.
        
    Returns:
        Updated state dictionary.
    """
    if state is None:
        state = load_state(project_root)
    
    current_time = datetime.now(timezone.utc).isoformat()
    normalized_path = artifact_path.replace(os.sep, '/')
    
    if "artifacts" not in state or normalized_path not in state["artifacts"]:
        logger.warning(f"Artifact not found in state: {normalized_path}. Registering instead.")
        return register_artifact(artifact_path, "unknown", state, project_root)
    
    # Update timestamp
    state["artifacts"][normalized_path]["updated_at"] = current_time
    
    # Update global timestamp (Constitution Principle V)
    state["updated_at"] = current_time
    
    save_state(state, project_root)
    
    logger.info(f"Updated timestamp for artifact: {normalized_path}")
    return state

def on_artifact_change(
    artifact_path: str,
    artifact_type: str,
    project_root: Optional[Path] = None
) -> None:
    """
    Convenience function to be called whenever an artifact is created or modified.
    
    This is the primary entry point for maintaining state consistency.
    
    Args:
        artifact_path: Relative path to the artifact.
        artifact_type: Type of artifact.
        project_root: Base directory for the project.
    """
    state = load_state(project_root)
    
    normalized_path = artifact_path.replace(os.sep, '/')
    
    if normalized_path in state.get("artifacts", {}):
        update_artifact_timestamp(artifact_path, state, project_root)
    else:
        register_artifact(artifact_path, artifact_type, state, project_root)

def get_artifact_info(
    artifact_path: str,
    project_root: Optional[Path] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieve information about a specific artifact.
    
    Args:
        artifact_path: Relative path to the artifact.
        project_root: Base directory for the project.
        
    Returns:
        Dictionary containing artifact info, or None if not found.
    """
    state = load_state(project_root)
    normalized_path = artifact_path.replace(os.sep, '/')
    
    return state.get("artifacts", {}).get(normalized_path)