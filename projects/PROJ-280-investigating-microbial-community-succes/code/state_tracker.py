import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# Project root is assumed to be the parent of 'code' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-280-investigating-microbial-community-succes.yaml"

def ensure_state_file():
    """Ensure the state tracking YAML file exists. Creates it if missing."""
    if not STATE_FILE_PATH.exists():
        STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Initialize with an empty artifacts dictionary
        initial_state = {
            "project_id": "PROJ-280-investigating-microbial-community-succes",
            "artifacts": {}
        }
        with open(STATE_FILE_PATH, 'w') as f:
            yaml.dump(initial_state, f, default_flow_style=False, sort_keys=False)
        return True
    return False

def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state() -> Dict[str, Any]:
    """Load the current state from the YAML file."""
    ensure_state_file()
    with open(STATE_FILE_PATH, 'r') as f:
        return yaml.safe_load(f)

def save_state(state: Dict[str, Any]):
    """Save the state to the YAML file."""
    ensure_state_file()
    with open(STATE_FILE_PATH, 'w') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def update_artifact_hash(artifact_path: str) -> Dict[str, Any]:
    """
    Calculate the hash of a file and update the state tracking file.
    
    Args:
        artifact_path: Relative path from project root to the artifact.
        
    Returns:
        The updated artifact entry in the state.
    """
    full_path = PROJECT_ROOT / artifact_path
    if not full_path.exists():
        raise FileNotFoundError(f"Cannot update hash: artifact not found at {full_path}")
    
    file_hash = calculate_file_hash(full_path)
    state = load_state()
    
    if "artifacts" not in state:
        state["artifacts"] = {}
        
    state["artifacts"][artifact_path] = {
        "hash": file_hash,
        "hash_algorithm": "sha256",
        "last_updated": str(full_path.stat().st_mtime)
    }
    
    save_state(state)
    return state["artifacts"][artifact_path]

def update_multiple_artifacts(artifact_paths: list) -> Dict[str, Any]:
    """
    Update hashes for multiple artifacts in a single operation.
    
    Args:
        artifact_paths: List of relative paths from project root.
        
    Returns:
        The updated state dictionary.
    """
    state = load_state()
    if "artifacts" not in state:
        state["artifacts"] = {}
        
    for rel_path in artifact_paths:
        full_path = PROJECT_ROOT / rel_path
        if full_path.exists():
            file_hash = calculate_file_hash(full_path)
            state["artifacts"][rel_path] = {
                "hash": file_hash,
                "hash_algorithm": "sha256",
                "last_updated": str(full_path.stat().st_mtime)
            }
        else:
            # Optionally log a warning or remove the key if the file is gone
            if rel_path in state["artifacts"]:
                del state["artifacts"][rel_path]
    
    save_state(state)
    return state

def get_artifact_hash(artifact_path: str) -> Optional[str]:
    """
    Retrieve the stored hash for an artifact.
    
    Args:
        artifact_path: Relative path from project root.
        
    Returns:
        The stored hash string, or None if not found.
    """
    state = load_state()
    if "artifacts" in state and artifact_path in state["artifacts"]:
        return state["artifacts"][artifact_path].get("hash")
    return None

def verify_artifact_integrity(artifact_path: str) -> bool:
    """
    Verify that the current file hash matches the stored hash.
    
    Args:
        artifact_path: Relative path from project root.
        
    Returns:
        True if hashes match, False otherwise.
        
    Raises:
        FileNotFoundError: If the artifact does not exist.
    """
    full_path = PROJECT_ROOT / artifact_path
    if not full_path.exists():
        raise FileNotFoundError(f"Cannot verify integrity: artifact not found at {full_path}")
    
    current_hash = calculate_file_hash(full_path)
    stored_hash = get_artifact_hash(artifact_path)
    
    if stored_hash is None:
        return False
        
    return current_hash == stored_hash

def list_all_artifacts() -> Dict[str, Dict[str, Any]]:
    """
    List all tracked artifacts and their metadata.
    
    Returns:
        Dictionary of artifact paths to their metadata.
    """
    state = load_state()
    return state.get("artifacts", {})

def clear_artifact(artifact_path: str):
    """
    Remove an artifact from the tracking state.
    
    Args:
        artifact_path: Relative path from project root.
    """
    state = load_state()
    if "artifacts" in state and artifact_path in state["artifacts"]:
        del state["artifacts"][artifact_path]
        save_state(state)

def main():
    """
    CLI entry point for state tracking operations.
    Usage:
      python code/state_tracker.py update <relative_path>
      python code/state_tracker.py verify <relative_path>
      python code/state_tracker.py list
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python state_tracker.py <command> [args]")
        print("Commands: update <path>, verify <path>, list")
        sys.exit(1)
        
    command = sys.argv[1]
    
    if command == "update":
        if len(sys.argv) < 3:
            print("Error: update requires a path argument")
            sys.exit(1)
        path = sys.argv[2]
        try:
            result = update_artifact_hash(path)
            print(f"Updated hash for {path}: {result['hash'][:16]}...")
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)
            
    elif command == "verify":
        if len(sys.argv) < 3:
            print("Error: verify requires a path argument")
            sys.exit(1)
        path = sys.argv[2]
        try:
            is_valid = verify_artifact_integrity(path)
            status = "VALID" if is_valid else "INVALID"
            print(f"Verification for {path}: {status}")
            if not is_valid:
                stored = get_artifact_hash(path)
                current = calculate_file_hash(PROJECT_ROOT / path)
                print(f"  Stored:  {stored}")
                print(f"  Current: {current}")
                sys.exit(1)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            sys.exit(1)
            
    elif command == "list":
        artifacts = list_all_artifacts()
        if not artifacts:
            print("No artifacts tracked yet.")
        else:
            print(f"Tracked artifacts ({len(artifacts)}):")
            for path, meta in artifacts.items():
                print(f"  {path}: {meta['hash'][:16]}...")
                
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
