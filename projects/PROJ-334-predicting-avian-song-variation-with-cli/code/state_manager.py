import os
import sys
import hashlib
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state(state_path: str) -> Dict[str, Any]:
    """Load state from a YAML file."""
    path = Path(state_path)
    if not path.exists():
        return {"artifact_hashes": {}}
        
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {"artifact_hashes": {}}

def save_state(state_path: str, state: Dict[str, Any]) -> None:
    """Save state to a YAML file."""
    path = Path(state_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)

def register_artifact(state_path: str, artifact_name: str, file_path: str) -> None:
    """Register an artifact in the state file."""
    state = load_state(state_path)
    file_hash = compute_file_hash(file_path)
    state["artifact_hashes"][artifact_name] = file_hash
    save_state(state_path, state)

def update_artifact(state_path: str, artifact_name: str, file_path: str) -> None:
    """Update an artifact's hash in the state file."""
    register_artifact(state_path, artifact_name, file_path)

def verify_artifact_integrity(state_path: str, artifact_name: str, file_path: str) -> bool:
    """Verify an artifact's integrity by comparing hashes."""
    state = load_state(state_path)
    stored_hash = state.get("artifact_hashes", {}).get(artifact_name)
    if not stored_hash:
        return False
    current_hash = compute_file_hash(file_path)
    return stored_hash == current_hash

def get_artifact_history(state_path: str, artifact_name: str) -> List[str]:
    """Get the history of an artifact (simplified to just current hash)."""
    state = load_state(state_path)
    hash_value = state.get("artifact_hashes", {}).get(artifact_name)
    return [hash_value] if hash_value else []

def list_all_artifacts(state_path: str) -> Dict[str, str]:
    """List all registered artifacts and their hashes."""
    state = load_state(state_path)
    return state.get("artifact_hashes", {})

def main():
    """Main entry point for state management."""
    print("State manager module loaded successfully.")
    print("Available functions: compute_file_hash, load_state, save_state, register_artifact, update_artifact, verify_artifact_integrity, get_artifact_history, list_all_artifacts")

if __name__ == "__main__":
    main()