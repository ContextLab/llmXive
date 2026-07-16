import os
import hashlib
import yaml
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path

def calculate_sha256(filepath: str) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state(state_path: str) -> Dict[str, Any]:
    """Load state from YAML file."""
    if not os.path.exists(state_path):
        return {"artifact_hashes": {}, "updated_at": None}
    with open(state_path, 'r') as f:
        return yaml.safe_load(f) or {"artifact_hashes": {}, "updated_at": None}

def update_state(state_path: str, artifact_name: str, new_hash: str):
    """Update state file with new artifact hash."""
    state = load_state(state_path)
    state["artifact_hashes"][artifact_name] = new_hash
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    with open(state_path, 'w') as f:
        yaml.dump(state, f)

def main():
    # Example usage
    csv_path = 'data/processed/simulation_results.csv'
    state_path = 'state/projects/PROJ-332-exploring-the-influence-of-network-topol.yaml'
    
    if os.path.exists(csv_path):
        h = calculate_sha256(csv_path)
        update_state(state_path, 'simulation_results.csv', h)
        print(f"Updated state with hash: {h}")
