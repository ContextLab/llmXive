"""
State tracking mechanism for the microbial community succession project.
Manages artifact hashes in the project state file.
"""
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

PROJECT_ROOT = Path(__file__).parent.parent
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-280-investigating-microbial-community-succes.yaml"

def _ensure_state_file():
    """Ensure the state directory and file exist."""
    STATE_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE_PATH.exists():
        initial_state = {
            "project_id": "PROJ-280-investigating-microbial-community-succes",
            "artifacts": {},
            "last_updated": None
        }
        with open(STATE_FILE_PATH, 'w') as f:
            yaml.dump(initial_state, f, default_flow_style=False)

def _load_state() -> Dict[str, Any]:
    """Load the current state from the YAML file."""
    _ensure_state_file()
    with open(STATE_FILE_PATH, 'r') as f:
        return yaml.safe_load(f)

def _save_state(state: Dict[str, Any]):
    """Save the state to the YAML file."""
    import datetime
    state['last_updated'] = datetime.datetime.now().isoformat()
    with open(STATE_FILE_PATH, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)

def calculate_file_hash(file_path: str) -> str:
    """
    Calculate SHA256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hexadecimal string of the SHA256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_artifact_hash(artifact_path: str, description: Optional[str] = None):
    """
    Update the hash for a specific artifact in the state file.
    
    Args:
        artifact_path: Relative path to the artifact from project root
        description: Optional description of the artifact
    """
    state = _load_state()
    
    if 'artifacts' not in state:
        state['artifacts'] = {}
        
    abs_path = PROJECT_ROOT / artifact_path
    if not abs_path.exists():
        raise FileNotFoundError(f"Artifact not found: {abs_path}")
    
    file_hash = calculate_file_hash(str(abs_path))
    
    state['artifacts'][artifact_path] = {
        'hash': file_hash,
        'description': description or f"Artifact: {artifact_path}",
        'updated': True
    }
    
    _save_state(state)

def update_multiple_artifacts(artifacts: Dict[str, Optional[str]]):
    """
    Update hashes for multiple artifacts at once.
    
    Args:
        artifacts: Dict mapping artifact_path to optional description
    """
    state = _load_state()
    if 'artifacts' not in state:
        state['artifacts'] = {}
        
    for artifact_path, description in artifacts.items():
        abs_path = PROJECT_ROOT / artifact_path
        if abs_path.exists():
            file_hash = calculate_file_hash(str(abs_path))
            state['artifacts'][artifact_path] = {
                'hash': file_hash,
                'description': description or f"Artifact: {artifact_path}",
                'updated': True
            }
    
    _save_state(state)

def get_artifact_hash(artifact_path: str) -> Optional[str]:
    """
    Get the stored hash for an artifact.
    
    Args:
        artifact_path: Relative path to the artifact
        
    Returns:
        Stored hash or None if not found
    """
    state = _load_state()
    if 'artifacts' not in state:
        return None
        
    return state['artifacts'].get(artifact_path, {}).get('hash')

def verify_artifact_integrity(artifact_path: str) -> bool:
    """
    Verify if an artifact's current hash matches the stored hash.
    
    Args:
        artifact_path: Relative path to the artifact
        
    Returns:
        True if hashes match, False otherwise
    """
    abs_path = PROJECT_ROOT / artifact_path
    if not abs_path.exists():
        return False
        
    current_hash = calculate_file_hash(str(abs_path))
    stored_hash = get_artifact_hash(artifact_path)
    
    return current_hash == stored_hash

def list_all_artifacts() -> Dict[str, Dict[str, Any]]:
    """
    List all tracked artifacts and their metadata.
    
    Returns:
        Dict mapping artifact paths to their metadata
    """
    state = _load_state()
    return state.get('artifacts', {})

def clear_artifact(artifact_path: str):
    """Remove an artifact from tracking."""
    state = _load_state()
    if 'artifacts' in state and artifact_path in state['artifacts']:
        del state['artifacts'][artifact_path]
        _save_state(state)

def main():
    """CLI entry point for state tracking operations."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python state_tracker.py <command> [args]")
        print("Commands: update, verify, list, get")
        sys.exit(1)
        
    command = sys.argv[1]
    
    if command == "update":
        if len(sys.argv) < 3:
            print("Error: Please provide artifact path")
            sys.exit(1)
        artifact_path = sys.argv[2]
        description = sys.argv[3] if len(sys.argv) > 3 else None
        update_artifact_hash(artifact_path, description)
        print(f"Updated hash for: {artifact_path}")
        
    elif command == "verify":
        if len(sys.argv) < 3:
            print("Error: Please provide artifact path")
            sys.exit(1)
        artifact_path = sys.argv[2]
        is_valid = verify_artifact_integrity(artifact_path)
        print(f"Artifact {artifact_path} integrity: {'VALID' if is_valid else 'INVALID'}")
        
    elif command == "list":
        artifacts = list_all_artifacts()
        print("Tracked artifacts:")
        for path, meta in artifacts.items():
            print(f"  {path}: {meta['hash'][:16]}...")
            
    elif command == "get":
        if len(sys.argv) < 3:
            print("Error: Please provide artifact path")
            sys.exit(1)
        artifact_path = sys.argv[2]
        hash_val = get_artifact_hash(artifact_path)
        if hash_val:
            print(f"Hash for {artifact_path}: {hash_val}")
        else:
            print(f"No hash found for {artifact_path}")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
