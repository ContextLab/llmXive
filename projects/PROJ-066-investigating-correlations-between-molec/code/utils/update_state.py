"""
State management utilities for the llmXive pipeline.

Handles loading, updating, and saving the project state YAML file,
including artifact hashes and verification.
"""
import os
import yaml
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Project root is assumed to be the current working directory when scripts are run.
# The state file location is relative to the project root.
STATE_DIR = Path("state") / "projects"

def compute_file_hash(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        RuntimeError: If an error occurs during hashing.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found for hashing: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error computing hash for {file_path}: {e}")

def get_artifact_hash(file_path: Path) -> str:
    """
    Alias for compute_file_hash.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    return compute_file_hash(file_path)

def load_state_file(project_id: str) -> Dict[str, Any]:
    """
    Loads the state file for a given project.
    Creates the file and necessary directories if they don't exist.
    
    Args:
        project_id: The unique identifier for the project.
        
    Returns:
        Dictionary containing the project state.
    """
    state_file_path = STATE_DIR / f"{project_id}.yaml"
    
    # Ensure directory exists
    state_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    if state_file_path.exists():
        with open(state_file_path, 'r') as f:
            content = yaml.safe_load(f)
            return content if content is not None else {}
    else:
        # Initialize a new state file
        return {
            "project_id": project_id,
            "last_updated": None,
            "artifacts": []
        }

def save_state_file(project_id: str, state: Dict[str, Any]) -> None:
    """
    Saves the state dictionary to the project's state file.
    
    Args:
        project_id: The unique identifier for the project.
        state: The dictionary containing the project state to save.
    """
    state_file_path = STATE_DIR / f"{project_id}.yaml"
    state_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_file_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def verify_artifact_integrity(project_id: str, artifact_path: str, expected_hash: str) -> bool:
    """
    Verifies the integrity of an artifact by recomputing its hash and comparing.
    
    Args:
        project_id: The unique identifier for the project (unused in logic but kept for context).
        artifact_path: Path to the artifact file.
        expected_hash: The expected SHA-256 hash string.
        
    Returns:
        True if the artifact hash matches the expected hash, False otherwise.
    """
    full_path = Path(artifact_path)
    if not full_path.is_absolute():
        # Assume relative to project root (CWD)
        full_path = Path.cwd() / artifact_path
        
    if not full_path.exists():
        return False
        
    try:
        actual_hash = compute_file_hash(full_path)
        return actual_hash == expected_hash
    except Exception:
        return False

def update_state(project_id: str, artifacts: List[Dict[str, Any]]) -> None:
    """
    Updates the project state file with new artifact information.
    
    This function ensures that the state file exists, updates the timestamp,
    and appends or updates the provided artifacts list.
    
    Args:
        project_id: The unique identifier for the project.
        artifacts: A list of dictionaries, each containing:
            - artifact_path: Relative path to the artifact.
            - hash: The SHA-256 hash of the artifact.
            - source: Optional source description.
            - version: Optional version string.
    """
    state = load_state_file(project_id)
    
    # Update timestamp
    state["last_updated"] = datetime.now().isoformat()
    
    # Add or update artifacts
    # We use a dictionary to track existing paths to handle updates efficiently
    existing_paths = {a.get("artifact_path"): a for a in state.get("artifacts", [])}
    
    for artifact in artifacts:
        path = artifact.get("artifact_path")
        if not path:
            raise ValueError("Each artifact must have an 'artifact_path' key.")
        
        if path in existing_paths:
            # Update existing entry
            existing_paths[path].update(artifact)
            existing_paths[path]["last_updated"] = datetime.now().isoformat()
        else:
            # Add new entry
            new_artifact = artifact.copy()
            new_artifact["last_updated"] = datetime.now().isoformat()
            state["artifacts"].append(new_artifact)
    
    # Reconstruct the list to maintain order (though dict order is preserved in Py3.7+)
    state["artifacts"] = list(existing_paths.values())
    
    save_state_file(project_id, state)