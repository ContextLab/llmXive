"""
update_state.py

Computes SHA-256 hashes for project artifacts and updates the project state file.

This script scans the `data/derived/` and `results/` directories, computes
SHA-256 hashes for all files, and writes a manifest to `state/projects/<project_id>/state.yaml`.
It also updates the `current_stage` to `implemented`.
"""
import os
import sys
import hashlib
import yaml
from pathlib import Path
from datetime import datetime

# Project constants
PROJECT_ID = "PROJ-150-detecting-statistical-power-drift-in-rep"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects" / PROJECT_ID
STATE_FILE = STATE_DIR / "state.yaml"
ARTIFACT_DIRS = [
    PROJECT_ROOT / "data" / "derived",
    PROJECT_ROOT / "results"
]

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        raise RuntimeError(f"Failed to compute hash for {file_path}: {e}")

def find_artifacts() -> list:
    """Find all files in the artifact directories."""
    artifacts = []
    for directory in ARTIFACT_DIRS:
        if not directory.exists():
            print(f"Warning: Artifact directory {directory} does not exist. Skipping.")
            continue
        
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                artifacts.append(file_path)
    return artifacts

def load_state() -> dict:
    """Load existing state file or create a new one."""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return yaml.safe_load(f) or {}
    return {
        "project_id": PROJECT_ID,
        "last_updated": None,
        "current_stage": "setup",
        "artifacts": {}
    }

def save_state(state: dict):
    """Save state to YAML file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def main():
    """Main entry point for updating project state."""
    print(f"Updating state for project: {PROJECT_ID}")
    
    # Load current state
    state = load_state()
    
    # Find and hash artifacts
    artifacts = find_artifacts()
    if not artifacts:
        print("No artifacts found to hash.")
    else:
        print(f"Found {len(artifacts)} artifact(s) to hash.")
        for file_path in artifacts:
            rel_path = file_path.relative_to(PROJECT_ROOT)
            file_hash = compute_sha256(file_path)
            state["artifacts"][str(rel_path)] = {
                "hash": file_hash,
                "size_bytes": file_path.stat().st_size
            }
            print(f"  Hashed: {rel_path}")
    
    # Update metadata
    state["last_updated"] = datetime.utcnow().isoformat() + "Z"
    state["current_stage"] = "implemented"
    
    # Save updated state
    save_state(state)
    print(f"State updated successfully: {STATE_FILE}")

if __name__ == "__main__":
    main()