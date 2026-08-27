#!/usr/bin/env python
# Implementation
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

def version_artifact(file_path: Path, state_dir: Path) -> Dict[str, Any]:
    """Version an artifact by calculating hash and size."""
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact not found: {file_path}")
    
    artifact_hash = calculate_sha256(file_path)
    size = get_file_size(file_path)
    
    version_info = {
        "path": str(file_path),
        "hash": artifact_hash,
        "size": size
    }
    
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "version_state.json"
    
    if state_file.exists():
        with open(state_file, "r") as f:
            state = json.load(f)
    else:
        state = {}
    
    state[file_path.name] = version_info
    
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)
        
    return version_info

def main():
    parser = argparse.ArgumentParser(description="Version artifacts")
    parser.add_argument("--file", type=str, required=True, help="Path to artifact")
    parser.add_argument("--state-dir", type=str, default="state", help="State directory")
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    file_path = Path(args.file)
    if not file_path.is_absolute():
        file_path = project_root / file_path
        
    state_dir = project_root / args.state_dir
    
    try:
        info = version_artifact(file_path, state_dir)
        print(f"Versioned {file_path}: {info}")
    except Exception as e:
        print(f"Error versioning artifact: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
