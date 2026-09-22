"""
Artifact Hashing and State Management.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Optional

def hash_file(file_path: str) -> str:
    """Calculates SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_state(state_file: str = "data/state.json"):
    """
    Updates the state file with hashes of recent artifacts.
    """
    state = {}
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            state = json.load(f)
    
    # Example: Hash the processed data if it exists
    processed_data = "data/processed/creep_data_processed.csv"
    if os.path.exists(processed_data):
        state['processed_data_hash'] = hash_file(processed_data)
    
    # Write back
    Path(state_file).parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)