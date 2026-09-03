#!/usr/bin/env python
"""
Versioning Module.
Calculates SHA256 hashes for artifacts and updates state.
"""
import argparse
import sys
import hashlib
import json
import os
from pathlib import Path

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    return file_path.stat().st_size

def version_artifact(file_path: Path, state_dir: Path):
    """Version an artifact by adding its hash to the state."""
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "artifact_versions.json"
    
    if state_file.exists():
        with open(state_file, "r") as f:
            state = json.load(f)
    else:
        state = {"artifacts": {}}
    
    hash_val = calculate_sha256(file_path)
    size = get_file_size(file_path)
    
    state["artifacts"][file_path.name] = {
        "hash": hash_val,
        "size": size,
        "path": str(file_path)
    }
    
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description="Version artifacts")
    parser.add_argument("--file", type=str, required=True, help="Path to file to version")
    args = parser.parse_args()
    
    project_root = Path(__file__).resolve().parent.parent
    state_dir = project_root / "state"
    
    try:
        file_path = Path(args.file).resolve()
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return 1
        
        version_artifact(file_path, state_dir)
        print(f"Versioned artifact: {file_path}")
    except Exception as e:
        print(f"Error versioning artifact: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
