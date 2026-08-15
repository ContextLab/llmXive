"""
Hygiene module for PROJ-163: Compute SHA256 checksums for data artifacts
and update the project state YAML file with artifact hashes.

This script ensures data integrity by verifying checksums of all files
in the data/ directory and persisting them to the state file.
"""

import hashlib
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Project root relative to this file's location (assuming code/ is a subdirectory)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
# The exact filename pattern based on the project ID
STATE_FILE_PREFIX = "PROJ-163-exploring-the-role-of-network-structure-"

def compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def get_relative_path(file_path: Path) -> str:
    """Get path relative to project root."""
    return str(file_path.relative_to(PROJECT_ROOT))

def find_state_file() -> Optional[Path]:
    """Find the project state YAML file."""
    if STATE_DIR.exists():
        # Look for files starting with the project ID
        candidates = list(STATE_DIR.glob(f"{STATE_FILE_PREFIX}*.yaml"))
        if candidates:
            return candidates[0]
    return None

def load_state(state_path: Path) -> Dict[str, Any]:
    """Load existing state or return a default structure."""
    if state_path.exists():
        with open(state_path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
            return content if content else {}
    return {
        "project_id": STATE_FILE_PREFIX,
        "last_updated": None,
        "artifacts": {}
    }

def save_state(state_path: Path, state: Dict[str, Any]) -> None:
    """Save state dictionary to YAML file."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def process_data_directory() -> Dict[str, str]:
    """
    Traverse data/ directory and compute hashes for all files.
    Returns a dict mapping relative path -> sha256 hash.
    """
    if not DATA_DIR.exists():
        print(f"Warning: Data directory {DATA_DIR} does not exist.")
        return {}

    hashes = {}
    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            file_path = Path(root) / file
            if file_path.is_file():
                rel_path = get_relative_path(file_path)
                try:
                    file_hash = compute_sha256(file_path)
                    hashes[rel_path] = file_hash
                    print(f"Computed hash for: {rel_path} -> {file_hash[:16]}...")
                except Exception as e:
                    print(f"Error computing hash for {rel_path}: {e}")
    return hashes

def update_state_file(hashes: Dict[str, str]) -> None:
    """Update the project state file with new artifact hashes."""
    state_path = find_state_file()
    if not state_path:
        # If no state file exists, create one in the expected location
        state_path = STATE_DIR / f"{STATE_FILE_PREFIX}.yaml"
        print(f"Creating new state file at: {state_path}")

    state = load_state(state_path)
    
    # Update artifacts with the new hashes
    state["artifacts"] = hashes
    
    # Update timestamp
    state["last_updated"] = datetime.utcnow().isoformat()
    
    save_state(state_path, state)
    print(f"State file updated at: {state_path}")
    print(f"Total artifacts tracked: {len(hashes)}")

def main():
    """Main entry point for the hygiene script."""
    print("Starting hygiene check for PROJ-163...")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Data Dir: {DATA_DIR}")

    # Step 1: Compute hashes
    hashes = process_data_directory()
    
    # Step 2: Update state file (even if empty, to reflect current state)
    update_state_file(hashes)
    
    if not hashes:
        print("No data files found to hash. State updated with empty artifacts.")
    else:
        print("Hygiene check completed successfully.")

if __name__ == "__main__":
    main()