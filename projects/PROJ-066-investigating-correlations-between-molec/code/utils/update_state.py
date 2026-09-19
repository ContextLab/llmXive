"""
State management utilities for the project pipeline.
Handles loading, updating, and saving the project state file with artifact hashes.
"""
import os
import yaml
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Project root is assumed to be the parent of the 'code' directory
# This path logic must be consistent with how the script is invoked
project_root = Path(__file__).resolve().parent.parent.parent
STATE_DIR = project_root / "state" / "projects"
STATE_FILE_NAME = "PROJ-066-investigating-correlations-between-molec.yaml"

def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Computes the hash of a file using the specified algorithm.
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            hash_func.update(byte_block)
    return hash_func.hexdigest()

def get_artifact_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Wrapper to compute artifact hash, raising if file not found.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot compute hash: file not found at {file_path}")
    return compute_file_hash(file_path, algorithm)

def load_state_file(state_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Loads the state file. If it doesn't exist, returns a default structure.
    """
    if state_path is None:
        state_path = STATE_DIR / STATE_FILE_NAME
    
    if not state_path.exists():
        # Ensure directory exists
        state_path.parent.mkdir(parents=True, exist_ok=True)
        return {
            "project_id": "PROJ-066-investigating-correlations-between-molec",
            "last_updated": None,
            "artifacts": []
        }
    
    with open(state_path, "r") as f:
        return yaml.safe_load(f) or {
            "project_id": "PROJ-066-investigating-correlations-between-molec",
            "last_updated": None,
            "artifacts": []
        }

def save_state_file(state_data: Dict[str, Any], state_path: Optional[Path] = None) -> None:
    """
    Saves the state data to the YAML file.
    """
    if state_path is None:
        state_path = STATE_DIR / STATE_FILE_NAME
    
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_path, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

def verify_artifact_integrity(file_path: Path, expected_hash: str) -> bool:
    """
    Verifies if a file's hash matches the expected hash.
    """
    if not file_path.exists():
        return False
    computed_hash = compute_file_hash(file_path)
    return computed_hash == expected_hash

def update_state(project_id: str, artifacts: List[Dict[str, Any]]) -> None:
    """
    Updates the project state file with new artifact information.
    This function appends new artifacts or updates existing ones based on artifact_path.
    
    Args:
        project_id: The project identifier.
        artifacts: List of dicts containing 'artifact_path', 'hash', 'source', 'version', etc.
    """
    state_path = STATE_DIR / f"{project_id}.yaml"
    state_data = load_state_file(state_path)
    
    # Ensure project_id matches
    state_data["project_id"] = project_id
    state_data["last_updated"] = datetime.now().isoformat()
    
    # Update or append artifacts
    if "artifacts" not in state_data:
        state_data["artifacts"] = []
    
    current_artifacts = {a.get("artifact_path"): a for a in state_data["artifacts"]}
    
    for new_artifact in artifacts:
        path_key = new_artifact.get("artifact_path")
        if path_key:
            current_artifacts[path_key] = new_artifact
        else:
            # If no path key, just append (shouldn't happen in valid usage)
            state_data["artifacts"].append(new_artifact)
    
    state_data["artifacts"] = list(current_artifacts.values())
    
    save_state_file(state_data, state_path)
