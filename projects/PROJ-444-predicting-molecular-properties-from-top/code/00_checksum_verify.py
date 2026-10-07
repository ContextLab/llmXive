"""
T007: Implement SHA256 checksum verification for raw data (Constitution III).

This script computes SHA256 hashes of all files in data/raw/, records them
in data/checksums.txt, and updates the project state file with artifact_hashes.

It enforces fail-fast behavior: if data/raw/ is empty or missing, it exits
with SystemExit(1) and the message "Data Hygiene Failed: No raw data found to checksum."
"""

import hashlib
import os
import sys
import yaml
from pathlib import Path
from typing import List, Dict, Any

# Project root is the parent of the code/ directory
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
CHECKSUMS_FILE = PROJECT_ROOT / "data" / "checksums.txt"
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-444-predicting-molecular-properties-from-top.yaml"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def get_raw_data_files() -> List[Path]:
    """Get all files in data/raw/ directory."""
    if not DATA_RAW_DIR.exists():
        return []
    
    files = []
    for item in DATA_RAW_DIR.rglob("*"):
        if item.is_file():
            files.append(item)
    
    return sorted(files)

def write_checksums(files: List[Path], checksums: Dict[str, str]) -> None:
    """Write checksums to data/checksums.txt."""
    with open(CHECKSUMS_FILE, "w") as f:
        for file_path in files:
            relative_path = file_path.relative_to(PROJECT_ROOT)
            f.write(f"{checksums[str(file_path)]}  {relative_path}\n")

def load_state_file() -> Dict[str, Any]:
    """Load the project state file, creating it if it doesn't exist."""
    if not STATE_FILE.exists():
        # Create parent directories
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        return {"project": "PROJ-444-predicting-molecular-properties-from-top", "artifact_hashes": {}}
    
    with open(STATE_FILE, "r") as f:
        return yaml.safe_load(f) or {}

def save_state_file(state: Dict[str, Any]) -> None:
    """Save the project state file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def update_state_with_artifact_hashes(checksums: Dict[str, str]) -> None:
    """Update the state file with artifact hashes."""
    state = load_state_file()
    
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    # Update with new checksums
    for file_path, hash_value in checksums.items():
        relative_path = str(Path(file_path).relative_to(PROJECT_ROOT))
        state["artifact_hashes"][relative_path] = hash_value
    
    save_state_file(state)

def verify_checksums() -> bool:
    """Verify that recorded checksums match current file hashes."""
    if not CHECKSUMS_FILE.exists():
        return False
    
    recorded_checksums = {}
    with open(CHECKSUMS_FILE, "r") as f:
        for line in f:
            parts = line.strip().split("  ")
            if len(parts) == 2:
                hash_value, relative_path = parts
                recorded_checksums[relative_path] = hash_value
    
    # Verify each file
    for relative_path, recorded_hash in recorded_checksums.items():
        file_path = PROJECT_ROOT / relative_path
        if not file_path.exists():
            return False
        
        current_hash = compute_sha256(file_path)
        if current_hash != recorded_hash:
            return False
    
    return True

def main():
    """Main entry point for checksum verification."""
    # Check if data/raw/ exists and has files
    raw_files = get_raw_data_files()
    
    if not raw_files:
        print("Data Hygiene Failed: No raw data found to checksum.")
        sys.exit(1)
    
    # Compute checksums for all files
    checksums = {}
    for file_path in raw_files:
        file_hash = compute_sha256(file_path)
        checksums[str(file_path)] = file_hash
    
    # Write checksums to file
    write_checksums(raw_files, checksums)
    
    # Update state file with artifact hashes
    update_state_with_artifact_hashes(checksums)
    
    # Verify checksums were written correctly
    if not verify_checksums():
        print("Error: Checksum verification failed after writing.")
        sys.exit(1)
    
    print(f"Successfully computed checksums for {len(raw_files)} files.")
    print(f"Checksums written to: {CHECKSUMS_FILE}")
    print(f"State updated at: {STATE_FILE}")

if __name__ == "__main__":
    main()