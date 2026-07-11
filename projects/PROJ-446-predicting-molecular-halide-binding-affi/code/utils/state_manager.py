"""
State management for tracking artifacts and content hashing.
"""
import os
import json
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

STATE_FILE = "state.yaml"

def get_project_state_path() -> Path:
    """Get the path to the state file."""
    return Path(STATE_FILE)

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def calculate_directory_hash(dir_path: Path) -> str:
    """Calculate combined hash of all files in a directory."""
    combined_hash = hashlib.sha256()
    for file_path in sorted(dir_path.rglob("*")):
        if file_path.is_file():
            relative_path = file_path.relative_to(dir_path)
            combined_hash.update(relative_path.as_posix().encode())
            combined_hash.update(calculate_file_hash(file_path).encode())
    return combined_hash.hexdigest()

def load_state_yaml() -> Dict[str, Any]:
    """Load the state.yaml file."""
    state_path = get_project_state_path()
    if not state_path.exists():
        return {"artifacts": {}, "simulated_mode": False}
    with open(state_path, "r") as f:
        return yaml.safe_load(f) or {"artifacts": {}, "simulated_mode": False}

def save_state_yaml(state: Dict[str, Any]) -> None:
    """Save the state to state.yaml."""
    state_path = get_project_state_path()
    with open(state_path, "w") as f:
        yaml.safe_dump(state, f)

def update_artifact_hash(path: str, hash_value: str) -> None:
    """Update the hash for a specific artifact."""
    state = load_state_yaml()
    if "artifacts" not in state:
        state["artifacts"] = {}
    state["artifacts"][path] = hash_value
    save_state_yaml(state)

def set_simulated_mode(mode: bool) -> None:
    """Set the simulated mode flag."""
    state = load_state_yaml()
    state["simulated_mode"] = mode
    save_state_yaml(state)

def get_simulated_mode() -> bool:
    """Get the simulated mode flag."""
    state = load_state_yaml()
    return state.get("simulated_mode", False)

def generate_state_for_directory(dir_path: Path) -> Dict[str, str]:
    """Generate a hash map for all files in a directory."""
    result = {}
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            relative = str(file_path.relative_to(dir_path))
            result[relative] = calculate_file_hash(file_path)
    return result

def init_project_state() -> None:
    """Initialize the project state file."""
    state = {
        "artifacts": {},
        "simulated_mode": False,
        "created_at": "init"
    }
    save_state_yaml(state)
