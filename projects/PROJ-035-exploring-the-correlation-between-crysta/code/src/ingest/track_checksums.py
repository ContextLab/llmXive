"""
T006: Setup SHA-256 checksum tracking for raw data files.

This module scans the data/raw/ directory for all files, computes their
SHA-256 checksums, and updates the project state YAML file at:
state/projects/PROJ-035-exploring-the-correlation-between-crysta.yaml

This implements Constitution III (Data Provenance & Integrity).
"""
import os
import hashlib
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Project paths relative to repository root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = REPO_ROOT / "data" / "raw"
STATE_FILE = REPO_ROOT / "state" / "projects" / "PROJ-035-exploring-the-correlation-between-crysta.yaml"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def scan_directory(directory: Path) -> Dict[str, str]:
    """Scan a directory and return a dict of {relative_path: sha256_hash}."""
    checksums = {}
    if not directory.exists():
        return checksums
    
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            rel_path = str(file_path.relative_to(directory))
            checksums[rel_path] = compute_sha256(file_path)
    
    return checksums

def load_state(state_path: Path) -> Dict[str, Any]:
    """Load existing state file or create a new structure if it doesn't exist."""
    if state_path.exists():
        with open(state_path, "r") as f:
            return yaml.safe_load(f) or {}
    else:
        # Ensure parent directories exist
        state_path.parent.mkdir(parents=True, exist_ok=True)
        return {
            "project_id": "PROJ-035-exploring-the-correlation-between-crysta",
            "state_version": "1.0",
            "last_updated": None,
            "artifact_hashes": {}
        }

def save_state(state: Dict[str, Any], state_path: Path) -> None:
    """Save the state dictionary to the YAML file."""
    state["last_updated"] = datetime.utcnow().isoformat()
    with open(state_path, "w") as f:
        yaml.safe_dump(state, f, default_flow_style=False, sort_keys=False)

def update_checksums(raw_dir: Path, state_path: Path) -> Dict[str, str]:
    """
    Scan raw data directory, compute checksums, and update the state file.
    
    Returns the updated dictionary of checksums.
    """
    # Scan current files
    current_checksums = scan_directory(raw_dir)
    
    # Load existing state
    state = load_state(state_path)
    
    # Update artifact_hashes section with raw data checksums
    # We store them under a specific key to distinguish from other artifacts
    raw_data_key = "data/raw"
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    state["artifact_hashes"][raw_data_key] = current_checksums
    
    # Save updated state
    save_state(state, state_path)
    
    return current_checksums

def main() -> int:
    """Main entry point for checksum tracking."""
    print(f"Scanning raw data directory: {DATA_RAW_DIR}")
    
    if not DATA_RAW_DIR.exists():
        print(f"Warning: Raw data directory does not exist: {DATA_RAW_DIR}")
        print("Creating empty checksum entry in state file.")
    
    try:
        checksums = update_checksums(DATA_RAW_DIR, STATE_FILE)
        
        if not checksums:
            print("No files found in raw data directory.")
        else:
            print(f"Found {len(checksums)} file(s) in raw data directory:")
            for rel_path, hash_val in sorted(checksums.items()):
                print(f"  {rel_path}: {hash_val[:16]}...")
        
        print(f"State file updated: {STATE_FILE}")
        return 0
        
    except Exception as e:
        print(f"Error updating checksums: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
