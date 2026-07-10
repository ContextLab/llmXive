"""
State management module for calculating and persisting SHA-256 checksums.
Used to track integrity of data artifacts and update the project state file.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE_NAME = "PROJ-298-statistical-analysis-of-publicly-availab.yaml"
STATE_FILE_PATH = STATE_DIR / STATE_FILE_NAME

# Artifacts to hash for the initial state (Phase 2 completion)
# Based on completed tasks T001-T008
INITIAL_ARTIFACTS = [
    "data/events/reference_calendar.json",
    "data/taxonomy/survey_2023.json",
    "code/requirements.txt",
    "data/raw/.gitkeep",
    "data/processed/.gitkeep",
    "data/events/.gitkeep",
    "data/taxonomy/.gitkeep",
]


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None


def load_state() -> Dict[str, Any]:
    """Load existing state file or return empty structure."""
    if not STATE_FILE_PATH.exists():
        return {
            "project_id": "PROJ-298-statistical-analysis-of-publicly-availab",
            "last_updated": None,
            "artifacts": {}
        }
    
    with open(STATE_FILE_PATH, "r") as f:
        return yaml.safe_load(f) or {}


def save_state(state: Dict[str, Any]) -> None:
    """Save state dictionary to YAML file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Update timestamp
    from datetime import datetime
    state["last_updated"] = datetime.utcnow().isoformat()
    
    with open(STATE_FILE_PATH, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)


def update_artifact_checksums(artifact_paths: List[str]) -> Dict[str, str]:
    """
    Calculate checksums for a list of artifact paths relative to project root.
    Returns a dictionary of path -> checksum.
    """
    checksums = {}
    for rel_path in artifact_paths:
        full_path = PROJECT_ROOT / rel_path
        if full_path.exists():
            checksum = calculate_sha256(full_path)
            if checksum:
                checksums[rel_path] = checksum
        else:
            # Log warning but continue
            print(f"Warning: Artifact not found for hashing: {full_path}")
    
    return checksums


def initialize_state_file() -> None:
    """
    Initialize the state file with checksums for initial artifacts.
    This function is designed to be called after Phase 2 setup tasks.
    """
    # Load existing state or create new
    state = load_state()
    
    # Ensure project ID is set
    state["project_id"] = "PROJ-298-statistical-analysis-of-publicly-availab"
    
    # Calculate checksums for initial artifacts
    new_checksums = update_artifact_checksums(INITIAL_ARTIFACTS)
    
    # Merge with existing artifacts
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    state["artifacts"].update(new_checksums)
    
    # Save updated state
    save_state(state)
    
    print(f"State file initialized at: {STATE_FILE_PATH}")
    print(f"Checksums calculated for {len(new_checksums)} artifacts:")
    for path, checksum in new_checksums.items():
        print(f"  - {path}: {checksum[:16]}...")


def main():
    """Entry point for initializing state file."""
    initialize_state_file()


if __name__ == "__main__":
    main()
