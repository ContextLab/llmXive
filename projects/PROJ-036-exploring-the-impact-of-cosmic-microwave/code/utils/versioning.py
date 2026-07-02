"""
Versioning utility for llmXive research pipeline.
Calculates SHA256 hashes for all artifacts and updates the state file.
"""
import hashlib
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List

# Project root is assumed to be the parent of the 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects"

# Pattern to identify project directories (PROJ-XXXX-...)
# The task description implies we extract the project ID from config or directory name.
# We will scan the state/projects directory for matching IDs.
TARGET_PROJECT_ID = "PROJ-036-exploring-the-impact-of-cosmic-microwave"

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise RuntimeError(f"Failed to hash {file_path}: {e}")

def find_artifacts(root_path: Path) -> List[Path]:
    """
    Recursively find all relevant artifacts (code, data, configs) to hash.
    Excludes: __pycache__, .git, .pyc, .yaml (unless in data/raw or specific), 
            and temporary files.
    """
    artifacts = []
    ignore_dirs = {"__pycache__", ".git", ".tox", "node_modules", ".pytest_cache"}
    ignore_extensions = {".pyc", ".pyo", ".so", ".dll", ".exe"}
    
    # We want to hash:
    # 1. All .py files in code/
    # 2. All .yaml/.yml in config/ and data/ (except raw data which might be huge/binary)
    # 3. All .fits, .csv, .npy in data/processed, data/results
    
    # Strategy: Traverse specific directories known to contain versioned artifacts
    target_dirs = [
        PROJECT_ROOT / "code",
        PROJECT_ROOT / "config",
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "data" / "results",
        PROJECT_ROOT / "specs",
        PROJECT_ROOT / "contracts"
    ]
    
    for base_dir in target_dirs:
        if not base_dir.exists():
            continue
        
        for path in base_dir.rglob("*"):
            if path.is_file():
                # Skip ignored dirs
                if any(part in ignore_dirs for part in path.parts):
                    continue
                
                # Skip binary/compiled files
                if path.suffix in ignore_extensions:
                    continue
                
                # Skip raw data files (they are too large and binary, 
                # usually hashed by their own download process, but if we must, 
                # we can include .fits if they are small. 
                # For this task, we focus on config, code, and processed results).
                if "raw" in path.parts:
                    continue
                
                artifacts.append(path)
    
    return sorted(artifacts)

def get_project_state_path(project_id: str) -> Path:
    """Construct the path to the artifact_hashes.yaml for a given project."""
    state_path = STATE_DIR / project_id
    if not state_path.exists():
        state_path.mkdir(parents=True, exist_ok=True)
    return state_path / "artifact_hashes.yaml"

def update_artifact_hashes(project_id: str, artifacts: List[Path]) -> Dict[str, Any]:
    """
    Calculate hashes for artifacts and update the state file.
    Returns the new state dictionary.
    """
    hashes = {}
    for artifact in artifacts:
        try:
            rel_path = artifact.relative_to(PROJECT_ROOT)
            file_hash = calculate_sha256(artifact)
            hashes[str(rel_path)] = file_hash
        except Exception as e:
            print(f"Warning: Could not hash {artifact}: {e}")

    state_entry = {
        "project_id": project_id,
        "version": 1,
        "artifacts": hashes
    }
    
    state_file = get_project_state_path(project_id)
    
    # Load existing data if present to preserve other entries if any, 
    # though typically this file is specific to the project.
    existing_data = {}
    if state_file.exists():
        try:
            with open(state_file, "r") as f:
                existing_data = yaml.safe_load(f) or {}
        except yaml.YAMLError:
            existing_data = {}

    # Update with new hashes
    # We overwrite the 'artifacts' key for this run to ensure consistency
    existing_data.update(state_entry)
    
    with open(state_file, "w") as f:
        yaml.dump(existing_data, f, default_flow_style=False, sort_keys=False)
    
    return state_entry

def main():
    """Main entry point for the versioning utility."""
    print(f"Scanning for artifacts in project: {TARGET_PROJECT_ID}")
    
    if not STATE_DIR.exists():
        STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    artifacts = find_artifacts(PROJECT_ROOT)
    print(f"Found {len(artifacts)} artifacts to hash.")
    
    if not artifacts:
        print("No artifacts found to hash.")
        return

    try:
        state = update_artifact_hashes(TARGET_PROJECT_ID, artifacts)
        print(f"Successfully updated artifact hashes for {TARGET_PROJECT_ID}")
        print(f"State file: {get_project_state_path(TARGET_PROJECT_ID)}")
        print(f"Hashes generated for {len(state.get('artifacts', {}))} files.")
    except Exception as e:
        print(f"Error updating artifact hashes: {e}")
        raise

if __name__ == "__main__":
    main()
