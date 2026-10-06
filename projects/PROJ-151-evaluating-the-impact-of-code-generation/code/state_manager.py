import os
import hashlib
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

def initialize_state_file(state_path: Path) -> None:
    """
    Initialize the state.yaml file if it does not exist.
    Creates a skeleton with metadata and empty artifact registry.
    """
    if not state_path.exists():
        initial_state = {
            "project_id": "PROJ-151-evaluating-the-impact-of-code-generation",
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "artifacts": {}
        }
        with open(state_path, "w", encoding="utf-8") as f:
            yaml.dump(initial_state, f, default_flow_style=False, sort_keys=False)

def load_state(state_path: Path) -> Dict[str, Any]:
    """
    Load the current state from the state.yaml file.
    Raises FileNotFoundError if the state file does not exist.
    """
    if not state_path.exists():
        initialize_state_file(state_path)
    
    with open(state_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_state(state_path: Path, state: Dict[str, Any]) -> None:
    """
    Save the state dictionary to the state.yaml file.
    Updates the 'last_updated' timestamp.
    """
    state["last_updated"] = datetime.utcnow().isoformat()
    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate the SHA-256 hash of a file.
    Used for artifact integrity verification.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def register_artifact(
    state_path: Path, 
    artifact_name: str, 
    file_path: Path, 
    description: Optional[str] = None
) -> None:
    """
    Register a new artifact in the state.yaml file.
    Records the file path, hash, timestamp, and optional description.
    """
    state = load_state(state_path)
    
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    file_hash = calculate_file_hash(file_path)
    
    state["artifacts"][artifact_name] = {
        "path": str(file_path),
        "hash": file_hash,
        "registered_at": datetime.utcnow().isoformat(),
        "description": description or f"Artifact: {artifact_name}"
    }
    
    save_state(state_path, state)

def verify_artifact(state_path: Path, artifact_name: str) -> bool:
    """
    Verify that an artifact exists and its hash matches the recorded value.
    Returns True if valid, False otherwise.
    """
    state = load_state(state_path)
    
    if artifact_name not in state.get("artifacts", {}):
        return False
    
    record = state["artifacts"][artifact_name]
    file_path = Path(record["path"])
    
    if not file_path.exists():
        return False
    
    current_hash = calculate_file_hash(file_path)
    return current_hash == record["hash"]

def list_registered_artifacts(state_path: Path) -> Dict[str, Any]:
    """
    Return a dictionary of all registered artifacts and their metadata.
    """
    state = load_state(state_path)
    return state.get("artifacts", {})
