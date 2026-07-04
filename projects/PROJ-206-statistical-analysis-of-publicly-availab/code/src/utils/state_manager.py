import hashlib
import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_state_file_path(project_id: str) -> Path:
    """Get the path to the state file for a project."""
    state_dir = Path("state/projects")
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / f"{project_id}.yaml"

def load_state(project_id: str) -> Dict[str, Any]:
    """Load state file for a project."""
    state_path = get_state_file_path(project_id)
    if not state_path.exists():
        return {"artifacts": []}
    with open(state_path, 'r') as f:
        return yaml.safe_load(f) or {"artifacts": []}

def update_state_artifact(project_id: str, artifact_path: str, hash_value: str, timestamp: str) -> None:
    """Update the state file with a new artifact entry."""
    state = load_state(project_id)
    if "artifacts" not in state:
        state["artifacts"] = []
    
    # Check if artifact already exists and update, or add new
    found = False
    for artifact in state["artifacts"]:
        if artifact.get("path") == artifact_path:
            artifact["hash"] = hash_value
            artifact["updated_at"] = timestamp
            found = True
            break
    
    if not found:
        state["artifacts"].append({
            "path": artifact_path,
            "hash": hash_value,
            "created_at": timestamp,
            "updated_at": timestamp
        })
    
    state_path = get_state_file_path(project_id)
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)

def verify_artifact_integrity(project_id: str, artifact_path: str) -> bool:
    """Verify the integrity of an artifact by comparing its hash."""
    state = load_state(project_id)
    full_path = Path.cwd() / artifact_path
    if not full_path.exists():
        return False
    
    current_hash = compute_file_hash(full_path)
    
    for artifact in state.get("artifacts", []):
        if artifact.get("path") == artifact_path:
            stored_hash = artifact.get("hash")
            return current_hash == stored_hash
    
    return False

def main():
    """Main entry point for state manager (for testing)."""
    pass

if __name__ == "__main__":
    main()