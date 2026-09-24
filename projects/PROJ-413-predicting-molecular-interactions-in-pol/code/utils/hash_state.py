"""
Utility functions for computing SHA256 hashes and managing state files.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from utils.exceptions import DataError

def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA256 hash.
        
    Raises:
        DataError: If the file does not exist.
    """
    if not file_path.exists():
        raise DataError(f"File not found for hashing: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()

def hash_directory(dir_path: Path) -> Dict[str, str]:
    """
    Compute SHA256 hashes for all files in a directory recursively.
    
    Args:
        dir_path: Path to the directory.
        
    Returns:
        Dictionary mapping relative file paths to their SHA256 hashes.
    """
    hashes = {}
    if not dir_path.exists() or not dir_path.is_dir():
        return hashes
    
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(dir_path)
            hashes[str(rel_path)] = compute_sha256(file_path)
    
    return hashes

def update_state_yaml(state_path: Path, key_path: str, value: Any) -> None:
    """
    Update a specific key in the state YAML file with a new value.
    
    Args:
        state_path: Path to the state YAML file.
        key_path: Dot-separated path to the key (e.g., 'artifact_hashes.curated_dataset').
        value: The value to set.
        
    Raises:
        DataError: If the state file does not exist.
    """
    if not state_path.exists():
        raise DataError(f"State file not found: {state_path}")
    
    with open(state_path, 'r') as f:
        state_data = yaml.safe_load(f) or {}
    
    keys = key_path.split('.')
    current = state_data
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    current[keys[-1]] = value
    
    with open(state_path, 'w') as f:
        yaml.dump(state_data, f, default_flow_style=False)

def verify_artifacts(state_path: Path, artifacts: Dict[str, Path]) -> bool:
    """
    Verify that artifacts exist and their hashes match the state file.
    
    Args:
        state_path: Path to the state YAML file.
        artifacts: Dictionary mapping artifact names to their file paths.
        
    Returns:
        True if all artifacts match, False otherwise.
    """
    if not state_path.exists():
        raise DataError(f"State file not found: {state_path}")
    
    with open(state_path, 'r') as f:
        state_data = yaml.safe_load(f) or {}
    
    artifact_hashes = state_data.get('artifact_hashes', {})
    all_match = True
    
    for name, path in artifacts.items():
        if not path.exists():
            print(f"Artifact missing: {path}")
            all_match = False
            continue
        
        current_hash = compute_sha256(path)
        expected_hash = artifact_hashes.get(name)
        
        if expected_hash != current_hash:
            print(f"Hash mismatch for {name}: expected {expected_hash}, got {current_hash}")
            all_match = False
        else:
            print(f"Verified {name}: {current_hash}")
    
    return all_match

def get_state_hash(state_path: Path) -> Optional[str]:
    """
    Get the overall state hash from the state file.
    
    Args:
        state_path: Path to the state YAML file.
        
    Returns:
        The state hash or None if not present.
    """
    if not state_path.exists():
        return None
    
    with open(state_path, 'r') as f:
        state_data = yaml.safe_load(f) or {}
    
    return state_data.get('state_hash')

def main():
    """
    Main function to demonstrate hash computation and state updates.
    This script is designed to be run as part of the pipeline to update
    state hashes for generated artifacts.
    """
    import sys
    from pathlib import Path
    
    # Determine project root (parent of code/utils)
    project_root = Path(__file__).resolve().parent.parent.parent
    
    # Define paths relative to project root
    state_file = project_root / "state" / "projects" / "PROJ-413-predicting-molecular-interactions-in-pol.yaml"
    
    # Define artifacts to hash based on task requirements
    # T002 focuses on setting up the utility, but main() should demonstrate
    # usage on real artifacts if they exist, or handle missing gracefully
    artifacts_to_hash = {
        "curated_dataset": project_root / "data" / "curated" / "curated_dataset.csv",
        "descriptors": project_root / "data" / "processed" / "descriptors.csv",
        "graphs": project_root / "data" / "processed" / "graphs.pt",
        "model": project_root / "results" / "model.pt",
        "stats": project_root / "results" / "stats.csv",
        "attribution": project_root / "results" / "attribution.json",
        "performance": project_root / "results" / "performance.json"
    }
    
    if not state_file.exists():
        print(f"State file not found: {state_file}")
        # Create the directory structure if it doesn't exist to allow future runs
        state_file.parent.mkdir(parents=True, exist_ok=True)
        # Initialize an empty state file
        with open(state_file, 'w') as f:
            yaml.dump({"state_hash": None, "artifact_hashes": {}}, f, default_flow_style=False)
        print(f"Initialized empty state file at {state_file}")
        return
    
    with open(state_file, 'r') as f:
        state_data = yaml.safe_load(f) or {}
    
    if 'artifact_hashes' not in state_data:
        state_data['artifact_hashes'] = {}
    
    updated = False
    for name, path in artifacts_to_hash.items():
        if path.exists():
            try:
                hash_value = compute_sha256(path)
                if state_data['artifact_hashes'].get(name) != hash_value:
                    state_data['artifact_hashes'][name] = hash_value
                    updated = True
                    print(f"Hashed {name}: {hash_value}")
                else:
                    print(f"Hash unchanged for {name}")
            except Exception as e:
                print(f"Error hashing {name} ({path}): {e}")
        else:
            # If the artifact doesn't exist, we don't remove the hash, 
            # but we note it's missing. In a real pipeline, this might be a warning.
            print(f"Artifact not found (skipping hash): {path}")
    
    if updated:
        with open(state_file, 'w') as f:
            yaml.dump(state_data, f, default_flow_style=False)
        print(f"Updated state file at {state_file}")
    else:
        print("No updates required for state file.")

if __name__ == "__main__":
    main()