import os
import hashlib
import yaml
import glob
from typing import Dict, Any, Optional, List
from pathlib import Path
from config import get_project_root

STATE_FILE = "state/projects/PROJ-196-the-role-of-temporal-discounting-in-proc.yaml"

def ensure_state_file() -> Path:
    """Ensures the state file exists and creates it if missing."""
    path = get_project_root() / STATE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with open(path, "w") as f:
            yaml.dump({"artifact_hashes": {}}, f)
    return path

def calculate_file_hash(file_path: Path) -> str:
    """Calculates SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_state() -> Dict[str, Any]:
    """Loads the current state."""
    path = ensure_state_file()
    with open(path, "r") as f:
        return yaml.safe_load(f) or {"artifact_hashes": {}}

def update_artifact_hash(path_str: str, hash_val: str):
    """Updates a single artifact hash in state."""
    state = get_state()
    state["artifact_hashes"][path_str] = hash_val
    with open(get_project_root() / STATE_FILE, "w") as f:
        yaml.dump(state, f)

def update_all_artifacts_in_directory(directory: str):
    """Scans a directory and updates hashes for all files."""
    directory_path = get_project_root() / directory
    if not directory_path.exists():
        return
    
    for file_path in directory_path.rglob("*"):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(get_project_root()))
            h = calculate_file_hash(file_path)
            update_artifact_hash(rel_path, h)

def update_artifacts_for_pipeline():
    """Updates hashes for all raw and processed data artifacts."""
    update_all_artifacts_in_directory("data/raw")
    update_all_artifacts_in_directory("data/processed")

def verify_artifacts() -> bool:
    """Verifies all recorded artifacts exist and match hashes."""
    state = get_state()
    for path_str, recorded_hash in state.get("artifact_hashes", {}).items():
        full_path = get_project_root() / path_str
        if not full_path.exists():
            return False
        current_hash = calculate_file_hash(full_path)
        if current_hash != recorded_hash:
            return False
    return True

def clear_artifact_hashes():
    """Clears all artifact hashes."""
    path = ensure_state_file()
    with open(path, "w") as f:
        yaml.dump({"artifact_hashes": {}}, f)

def main():
    """
    CLI entry point to update artifact hashes for the current pipeline run.
    This function scans data/raw and data/processed directories, calculates
    SHA256 hashes for every file, and updates the state YAML file.
    """
    print("Updating artifact hashes for data/raw and data/processed...")
    update_artifacts_for_pipeline()
    print(f"State file updated at: {get_project_root() / STATE_FILE}")

if __name__ == "__main__":
    main()