"""
Data Checksum Generation and State File Update Tool

Implements Constitution Principle III: Write data checksums to data/checksums.csv
AND update the state file artifact_hashes map.

Usage:
    python code/data/checksums.py
"""
import os
import sys
import hashlib
import csv
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
PROJECT_ID = "PROJ-141-evaluating-the-impact-of-code-generation"
STATE_FILE = STATE_DIR / f"{PROJECT_ID}.yaml"
CHECKSUM_FILE = DATA_DIR / "checksums.csv"


def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute the hash of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def scan_data_directory(data_dir: Path) -> List[Dict[str, Any]]:
    """Scan the data directory for all files and compute their checksums."""
    checksums = []
    
    if not data_dir.exists():
        print(f"Warning: Data directory does not exist: {data_dir}")
        return checksums
    
    for file_path in data_dir.rglob("*"):
        if file_path.is_file():
            # Skip the checksum file itself to avoid circular dependency
            if file_path == CHECKSUM_FILE:
                continue
            
            try:
                file_hash = compute_file_hash(file_path)
                relative_path = file_path.relative_to(data_dir)
                checksums.append({
                    "path": str(relative_path),
                    "hash": file_hash,
                    "algorithm": "sha256",
                    "size_bytes": file_path.stat().st_size,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            except Exception as e:
                print(f"Error computing hash for {file_path}: {e}")
    
    return checksums


def write_checksums_csv(checksums: List[Dict[str, Any]], output_path: Path):
    """Write the checksums to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ["path", "hash", "algorithm", "size_bytes", "timestamp"]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(checksums)
    
    print(f"Wrote {len(checksums)} checksums to {output_path}")


def update_state_file(checksums: List[Dict[str, Any]], state_file: Path):
    """Update the state file with the artifact_hashes map."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state or create new
    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            state_data = yaml.safe_load(f) or {}
    else:
        state_data = {
            "project_id": PROJECT_ID,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "artifact_hashes": {}
        }
    
    # Update timestamp
    state_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Build artifact_hashes map: path -> hash
    artifact_hashes = {}
    for entry in checksums:
        artifact_hashes[entry["path"]] = entry["hash"]
    
    state_data["artifact_hashes"] = artifact_hashes
    
    # Write back
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    
    print(f"Updated state file: {state_file}")


def main():
    """Main entry point for checksum generation and state update."""
    print(f"Starting checksum generation for project: {PROJECT_ID}")
    print(f"Data directory: {DATA_DIR}")
    print(f"State file: {STATE_FILE}")
    print(f"Output CSV: {CHECKSUM_FILE}")
    
    # Scan data directory
    checksums = scan_data_directory(DATA_DIR)
    
    if not checksums:
        print("No files found to checksum in data directory.")
        # Still update state file with empty map if it exists
        if STATE_FILE.exists():
            update_state_file([], STATE_FILE)
        return
    
    # Write CSV
    write_checksums_csv(checksums, CHECKSUM_FILE)
    
    # Update state file
    update_state_file(checksums, STATE_FILE)
    
    print("Checksum generation and state update completed successfully.")


if __name__ == "__main__":
    main()
