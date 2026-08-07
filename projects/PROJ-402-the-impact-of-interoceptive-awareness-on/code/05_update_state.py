"""
State Update Script for llmXive Pipeline.

Implements Constitution Principle V:
Compute SHA-256 hashes for all artifacts in data/ and results/
and update the project state YAML file.
"""
import hashlib
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import yaml

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE_NAME = "001-impact-of-interoceptive-awareness.yaml"
STATE_FILE_PATH = STATE_DIR / STATE_FILE_NAME

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        raise RuntimeError(f"Failed to compute hash for {file_path}: {e}")

def scan_directory_for_artifacts(directory: Path) -> List[Path]:
    """
    Recursively scan a directory for all files (excluding hidden files/dirs).
    Returns a list of Path objects for all files found.
    """
    if not directory.exists():
        return []
    
    artifacts = []
    for root, dirs, files in os.walk(directory):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.startswith('.'):
                continue
            artifacts.append(Path(root) / file)
    
    return sorted(artifacts)

def load_state_file(state_path: Path) -> Dict[str, Any]:
    """
    Load the existing state file or return a default structure if it doesn't exist.
    """
    if not state_path.exists():
        return {
            "project_id": "001-impact-of-interoceptive-awareness",
            "last_updated": None,
            "artifacts": {
                "data": {},
                "results": {}
            }
        }
    
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except (IOError, yaml.YAMLError) as e:
        raise RuntimeError(f"Failed to load state file {state_path}: {e}")

def update_state_file(state_path: Path, state: Dict[str, Any]) -> None:
    """
    Write the updated state dictionary to the YAML file.
    """
    # Ensure directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    except (IOError, OSError) as e:
        raise RuntimeError(f"Failed to write state file {state_path}: {e}")

def compute_artifact_hashes(base_dir: Path, state: Dict[str, Any]) -> None:
    """
    Compute hashes for all files in base_dir and update the state dictionary.
    """
    if not base_dir.exists():
        return

    artifacts = scan_directory_for_artifacts(base_dir)
    dir_name = base_dir.name
    
    if dir_name not in state["artifacts"]:
        state["artifacts"][dir_name] = {}

    current_hashes = {}
    
    for artifact_path in artifacts:
        relative_path = artifact_path.relative_to(base_dir)
        try:
            file_hash = compute_sha256(artifact_path)
            current_hashes[str(relative_path)] = file_hash
        except RuntimeError as e:
            print(f"Warning: {e}", file=sys.stderr)
            # Continue processing other files even if one fails

    # Update state for this directory
    state["artifacts"][dir_name] = current_hashes

def main():
    """
    Main entry point for the state update script.
    """
    print(f"Starting state update for project: {STATE_FILE_NAME}")
    
    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing state
    try:
        state = load_state_file(STATE_FILE_PATH)
    except RuntimeError as e:
        print(f"Error loading state: {e}", file=sys.stderr)
        sys.exit(1)

    # Update project metadata
    state["project_id"] = "001-impact-of-interoceptive-awareness"
    state["last_updated"] = datetime.utcnow().isoformat() + "Z"

    # Compute hashes for data/
    print(f"Scanning {DATA_DIR} for artifacts...")
    compute_artifact_hashes(DATA_DIR, state)

    # Compute hashes for results/
    print(f"Scanning {RESULTS_DIR} for artifacts...")
    compute_artifact_hashes(RESULTS_DIR, state)

    # Write updated state
    try:
        update_state_file(STATE_FILE_PATH, state)
        print(f"State file updated successfully: {STATE_FILE_PATH}")
    except RuntimeError as e:
        print(f"Error updating state: {e}", file=sys.stderr)
        sys.exit(1)

    # Summary
    data_count = len(state["artifacts"].get("data", {}))
    results_count = len(state["artifacts"].get("results", {}))
    print(f"Summary: {data_count} data artifacts, {results_count} result artifacts tracked.")

if __name__ == "__main__":
    main()
