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
from typing import Dict, Any

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    return file_path.stat().st_size

def version_artifact(file_path: Path, state_dir: Path):
    """Version an artifact by adding its hash to state."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "artifacts.json"

    if state_file.exists():
        with open(state_file, "r") as f:
            state = json.load(f)
    else:
        state = {}

    artifact_name = file_path.name
    state[artifact_name] = {
        "hash": calculate_sha256(file_path),
        "size": get_file_size(file_path),
        "path": str(file_path)
    }

    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)

    print(f"Versioned: {artifact_name} -> {state_file}")

def main():
    parser = argparse.ArgumentParser(description="Version artifacts")
    parser.add_argument("--files", nargs="+", required=True, help="Files to version")
    parser.add_argument("--state_dir", type=str, default="state", help="State directory")
    args = parser.parse_args()

    state_dir = Path(args.state_dir)
    for file_path in args.files:
        try:
            version_artifact(Path(file_path), state_dir)
        except Exception as e:
            print(f"Failed to version {file_path}: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()