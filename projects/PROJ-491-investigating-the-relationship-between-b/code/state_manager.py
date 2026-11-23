import hashlib
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import ensure_directories

STATE_FILE = "state/project_state.yaml"

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_directory_hash(dir_path: Path) -> Dict[str, str]:
    """Compute hashes for all files in a directory recursively."""
    hashes = {}
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            try:
                rel_path = file_path.relative_to(dir_path)
                hashes[str(rel_path)] = compute_file_hash(file_path)
            except ValueError:
                continue
    return hashes

def load_state() -> Dict[str, Any]:
    """Load the current project state from YAML."""
    ensure_directories()
    state_path = Path(STATE_FILE)
    if not state_path.exists():
        return {"artifacts": {}}
    with open(state_path, "r") as f:
        return yaml.safe_load(f) or {"artifacts": {}}

def save_state(state: Dict[str, Any]):
    """Save the project state to YAML."""
    ensure_directories()
    state_path = Path(STATE_FILE)
    with open(state_path, "w") as f:
        yaml.safe_dump(state, f, default_flow_style=False)

def _get_relative_path(file_path: Path) -> str:
    """
    Convert a file path to a project-relative string.
    Handles both absolute and relative input paths robustly.
    """
    # Resolve to absolute path to ensure consistency
    abs_path = file_path.resolve()
    
    # Get the project root (parent of the 'code' directory where this script lives)
    # or simply the current working directory if running from project root
    project_root = Path.cwd().resolve()
    
    try:
        # Try relative to current working directory first
        rel_path = abs_path.relative_to(project_root)
        return str(rel_path)
    except ValueError:
        # If that fails (e.g., path is outside cwd), try relative to home or just use the string
        # Fallback: if the path is absolute but not under cwd, we might need a different strategy.
        # However, in this project context, artifacts are expected under the project root.
        # If they are truly outside, we return the absolute path string to avoid crash,
        # though this might indicate a configuration error.
        return str(abs_path)

def update_state_artifact(file_path: Path):
    """Update the state with the hash of a specific file."""
    state = load_state()
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    # Use the robust relative path calculation
    rel_path = _get_relative_path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact not found for hashing: {file_path}")
        
    state["artifacts"][rel_path] = compute_file_hash(file_path)
    save_state(state)

def update_state_directory(dir_path: Path):
    """Update the state with hashes of all files in a directory."""
    state = load_state()
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    hashes = compute_directory_hash(dir_path)
    for rel_path, file_hash in hashes.items():
        state["artifacts"][rel_path] = file_hash
    save_state(state)

def verify_artifact_integrity(file_path: Path) -> bool:
    """Verify if a file's current hash matches the stored hash."""
    state = load_state()
    rel_path = _get_relative_path(file_path)
    
    if rel_path not in state.get("artifacts", {}):
        return False
    
    stored_hash = state["artifacts"][rel_path]
    current_hash = compute_file_hash(file_path)
    
    return stored_hash == current_hash

def main():
    # Example usage for CLI
    print("State manager initialized.")