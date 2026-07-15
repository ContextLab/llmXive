"""
Versioning and state management utilities.

Provides functions for SHA-256 hashing and state file management.
"""
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

# Project specific constant for state file path
PROJECT_STATE_FILE = "state/projects/PROJ-031-state.yaml"

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_directory_hash(dir_path: str) -> str:
    """Compute SHA-256 hash of all files in a directory."""
    sha256_hash = hashlib.sha256()
    dir_path = Path(dir_path)
    
    # Sort files for consistent ordering
    files = sorted(dir_path.rglob("*"))
    for file_path in files:
        if file_path.is_file():
            # Include relative path in hash
            relative_path = file_path.relative_to(dir_path)
            sha256_hash.update(str(relative_path).encode())
            # Include file content in hash
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()

def ensure_state_directory(base_path: str = "state/projects"):
    """Ensure the state directory exists."""
    state_dir = Path(base_path)
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir

def load_state(state_file: str = PROJECT_STATE_FILE) -> Dict[str, Any]:
    """Load state from a YAML file."""
    state_path = Path(state_file)
    if not state_path.exists():
        return {"artifacts": {}, "runs": [], "last_updated": None}
    
    with open(state_path, "r") as f:
        data = yaml.safe_load(f)
        return data if data is not None else {"artifacts": {}, "runs": [], "last_updated": None}

def save_state(state: Dict[str, Any], state_file: str = PROJECT_STATE_FILE):
    """Save state to a YAML file."""
    state_path = Path(state_file)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def update_artifact_state(artifact_path: str, state_file: str = PROJECT_STATE_FILE):
    """Update the state file with artifact information."""
    state = load_state(state_file)
    state["last_updated"] = datetime.now().isoformat()
    
    artifact_name = os.path.basename(artifact_path)
    relative_path = os.path.relpath(artifact_path)
    
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    state["artifacts"][artifact_name] = {
        "path": relative_path,
        "hash": compute_sha256(artifact_path),
        "updated": datetime.now().isoformat()
    }
    
    save_state(state, state_file)

def record_pipeline_run(state_file: str = PROJECT_STATE_FILE, metrics: Dict[str, Any] = None):
    """Record a pipeline run in the state file."""
    state = load_state(state_file)
    
    if "runs" not in state:
        state["runs"] = []
    
    run_record = {
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics or {}
    }
    
    state["runs"].append(run_record)
    state["last_updated"] = datetime.now().isoformat()
    
    save_state(state, state_file)

def get_artifact_hash(artifact_path: str) -> Optional[str]:
    """Get the hash of an artifact."""
    if not os.path.exists(artifact_path):
        return None
    return compute_sha256(artifact_path)

def verify_artifact_integrity(artifact_path: str, expected_hash: str, state_file: str = PROJECT_STATE_FILE) -> bool:
    """Verify the integrity of an artifact."""
    if not os.path.exists(artifact_path):
        return False
    
    actual_hash = compute_sha256(artifact_path)
    return actual_hash == expected_hash

def get_project_state_summary(state_file: str = PROJECT_STATE_FILE) -> Dict[str, Any]:
    """Get a summary of the project state."""
    state = load_state(state_file)
    
    summary = {
        "last_updated": state.get("last_updated"),
        "artifact_count": len(state.get("artifacts", {})),
        "run_count": len(state.get("runs", [])),
        "artifacts": list(state.get("artifacts", {}).keys())
    }
    
    return summary

def main():
    """Main entry point for versioning (demo)."""
    print("Versioning Module")
    print("Usage: from versioning import compute_sha256, compute_directory_hash, ensure_state_directory, load_state, save_state, update_artifact_state, record_pipeline_run, get_artifact_hash, verify_artifact_integrity, get_project_state_summary")

if __name__ == "__main__":
    main()