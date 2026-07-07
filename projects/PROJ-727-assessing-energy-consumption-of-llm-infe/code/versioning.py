"""
Versioning and artifact hashing logic.
"""
import hashlib
import os
import json
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
    """Updates a simple project state log with artifact hashes."""
    state_file = os.path.join(DATA_PROCESSED_DIR, "project_state.json")
    
    state = []
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            try:
                state = json.load(f)
            except json.JSONDecodeError:
                state = []

    new_entry = {
        "timestamp": datetime.now().isoformat(),
        "artifact": artifact_path,
        "hash": hash_file(artifact_path),
        "description": description
    }
    state.append(new_entry)

    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)
    
    print(f"Updated project state for: {artifact_path}")

if __name__ == "__main__":
    # Example usage for testing
    pass
