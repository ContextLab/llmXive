"""
State Manager Module

Computes SHA-256 hashes for derived artifacts and maintains the project state
in a YAML file under `state/`. This module ensures reproducibility by tracking
the exact content of generated data and model artifacts.
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import yaml

STATE_DIR = Path("state")
STATE_FILE = STATE_DIR / "project_state.yaml"

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
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")

def load_state() -> Dict[str, Any]:
    """
    Load the current project state from the YAML file.

    Returns:
        Dictionary containing the project state. If the file does not exist,
        returns an empty state structure.
    """
    if not STATE_FILE.exists():
        return {
            "version": "1.0",
            "last_updated": None,
            "artifacts": {}
        }

    try:
        with open(STATE_FILE, "r") as f:
            state = yaml.safe_load(f)
            if state is None:
                return {
                    "version": "1.0",
                    "last_updated": None,
                    "artifacts": {}
                }
            return state
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing state file {STATE_FILE}: {e}")

def save_state(state: Dict[str, Any]) -> None:
    """
    Save the project state to the YAML file.

    Args:
        state: The state dictionary to save.
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        yaml.safe_dump(state, f, default_flow_style=False, sort_keys=False)

def update_artifact_state(
    state: Dict[str, Any],
    artifact_path: str,
    file_path: Path,
    artifact_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update the state for a single artifact.

    Args:
        state: The current state dictionary.
        artifact_path: Relative path of the artifact (e.g., 'data/processed/descriptors.csv').
        file_path: Absolute path to the file on disk.
        artifact_type: Optional type label (e.g., 'dataset', 'model', 'report').

    Returns:
        Updated state dictionary.
    """
    if "artifacts" not in state:
        state["artifacts"] = {}

    hash_value = compute_sha256(file_path)
    
    artifact_entry = {
        "path": artifact_path,
        "hash": hash_value,
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }
    
    if artifact_type:
        artifact_entry["type"] = artifact_type

    state["artifacts"][artifact_path] = artifact_entry
    state["last_updated"] = datetime.utcnow().isoformat() + "Z"
    
    return state

def verify_artifact(state: Dict[str, Any], artifact_path: str) -> bool:
    """
    Verify that an artifact in the state matches its current file content.

    Args:
        state: The state dictionary.
        artifact_path: Relative path of the artifact.

    Returns:
        True if the hash matches, False otherwise.
    """
    if "artifacts" not in state or artifact_path not in state["artifacts"]:
        return False

    recorded_hash = state["artifacts"][artifact_path].get("hash")
    if not recorded_hash:
        return False

    file_path = Path(artifact_path)
    if not file_path.exists():
        return False

    current_hash = compute_sha256(file_path)
    return current_hash == recorded_hash

def update_state_for_multiple_artifacts(
    artifacts: List[Dict[str, Any]]
) -> None:
    """
    Update the global state file for multiple artifacts at once.

    Args:
        artifacts: List of dictionaries, each containing:
            - 'path': Relative path string
            - 'file_path': Path object to the file
            - 'type': Optional string type label
    """
    state = load_state()
    
    for item in artifacts:
        path_str = item["path"]
        file_path = item["file_path"]
        artifact_type = item.get("type")
        
        if not file_path.exists():
            raise FileNotFoundError(
                f"Cannot update state: file not found for artifact '{path_str}'"
            )
        
        state = update_artifact_state(
            state, 
            path_str, 
            file_path, 
            artifact_type
        )
    
    save_state(state)