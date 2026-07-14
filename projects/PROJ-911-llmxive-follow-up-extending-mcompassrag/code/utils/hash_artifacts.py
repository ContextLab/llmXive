"""
Utility to calculate SHA-256 hashes for data artifacts and update state.
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, Any
import yaml

from code.config import DATA_DIR, PROJECT_ROOT

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def hash_directory(dir_path: Path) -> Dict[str, str]:
    """Hash all files in a directory recursively."""
    hashes = {}
    if not dir_path.exists():
        return hashes
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(dir_path)
            hashes[str(rel_path)] = calculate_sha256(file_path)
    return hashes

def update_state_file():
    """Update the project state YAML file with artifact hashes."""
    state_dir = PROJECT_ROOT / "state" / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    # Use the specific project state file path as requested in T005
    state_file = state_dir / "PROJ-911-llmxive-follow-up-extending-mcompassrag.yaml"

    state_data = {
        "project": "PROJ-911-llmxive-follow-up-extending-mcompassrag",
        "artifacts": {}
    }

    # Hash processed and results data if they exist
    for data_subdir in ["processed", "results", "raw"]:
        sub_path = DATA_DIR / data_subdir
        if sub_path.exists():
            hashes = hash_directory(sub_path)
            if hashes:
                state_data["artifacts"][data_subdir] = hashes

    with open(state_file, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False)

if __name__ == "__main__":
    print("Hashing artifacts...")
    update_state_file()
    print("State updated.")
