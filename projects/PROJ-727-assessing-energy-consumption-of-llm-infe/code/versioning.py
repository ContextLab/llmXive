"""
Versioning and artifact hashing logic.
Updates project state in YAML format per Constitution Principle V.
"""
import hashlib
import os
import yaml
from pathlib import Path
from datetime import datetime

from code.config import DATA_PROCESSED_DIR

def hash_file(filepath):
    """Calculates SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_project_state(artifact_path, description):
    """Updates a project state log in YAML format with artifact hashes."""
    state_file = os.path.join(DATA_PROCESSED_DIR, "project_state.yaml")
    
    state = []
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            try:
                loaded_state = yaml.safe_load(f)
                state = loaded_state if loaded_state else []
            except yaml.YAMLError:
                state = []

    new_entry = {
        "timestamp": datetime.now().isoformat(),
        "artifact": artifact_path,
        "hash": hash_file(artifact_path),
        "description": description
    }
    state.append(new_entry)

    with open(state_file, "w") as f:
        yaml.safe_dump(state, f, default_flow_style=False, allow_unicode=True)
    
    print(f"Updated project state (YAML) for: {artifact_path}")

if __name__ == "__main__":
    # Example usage for testing
    pass