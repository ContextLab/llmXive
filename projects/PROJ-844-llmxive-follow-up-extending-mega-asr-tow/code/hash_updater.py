import os
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

def compute_file_hash(file_path: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state(state_path: str) -> Dict[str, Any]:
    """Load state YAML file."""
    with open(state_path, 'r') as f:
        return yaml.safe_load(f)

def save_state(state_path: str, state: Dict[str, Any]):
    """Save state YAML file."""
    with open(state_path, 'w') as f:
        yaml.dump(state, f)

def update_hashes(data_dir: str, state_path: str):
    """Update hashes for all files in data directory."""
    state = load_state(state_path)
    data_path = Path(data_dir)
    
    for file_path in data_path.rglob("*"):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(data_path))
            file_hash = compute_file_hash(str(file_path))
            state["hashes"][rel_path] = file_hash
    
    save_state(state_path, state)

def main():
    """Main entry point."""
    update_hashes("data/derived", "data/state.yaml")

if __name__ == "__main__":
    main()
