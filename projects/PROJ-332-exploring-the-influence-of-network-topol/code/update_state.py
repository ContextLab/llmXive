"""
State management module for tracking simulation progress and results.
Implements the Constitution Principle V: State updates with SHA-256 checksums.
"""

import os
import hashlib
import yaml
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path

# Project root relative to code directory
PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE = STATE_DIR / "PROJ-332-exploring-the-influence-of-network-topol.yaml"

def calculate_sha256(file_path: str) -> str:
    """
    Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hexadecimal SHA-256 hash string
        
    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
            
    return sha256_hash.hexdigest()

def load_state() -> Dict[str, Any]:
    """
    Load the project state file.
    
    Returns:
        Dictionary containing project state
        
    Raises:
        FileNotFoundError: If state file does not exist
        yaml.YAMLError: If state file is invalid YAML
    """
    if not STATE_FILE.exists():
        # Initialize empty state if file doesn't exist
        state = {
            "project_id": "PROJ-332-exploring-the-influence-of-network-topol",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "artifact_hashes": {},
            "tasks_completed": [],
            "last_run": None
        }
        # Ensure directory exists
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            yaml.dump(state, f, default_flow_style=False)
        return state
        
    with open(STATE_FILE, "r") as f:
        state = yaml.safe_load(f)
        
    return state

def update_state(
    artifact_name: str,
    artifact_path: str,
    task_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Update project state with new artifact hash and metadata.
    
    Args:
        artifact_name: Name of the artifact (e.g., "simulation_results.csv")
        artifact_path: Full path to the artifact file
        task_id: Optional task ID that produced this artifact
        metadata: Optional additional metadata to store
        
    Returns:
        Updated state dictionary
        
    Raises:
        FileNotFoundError: If artifact file does not exist
    """
    state = load_state()
    
    # Calculate hash
    if not os.path.exists(artifact_path):
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
        
    artifact_hash = calculate_sha256(artifact_path)
    
    # Update artifact hashes
    state["artifact_hashes"][artifact_name] = {
        "hash": artifact_hash,
        "path": artifact_path,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if task_id:
        if "tasks_completed" not in state:
            state["tasks_completed"] = []
        if task_id not in state["tasks_completed"]:
            state["tasks_completed"].append(task_id)
    
    if metadata:
        if "metadata" not in state:
            state["metadata"] = {}
        state["metadata"].update(metadata)
    
    # Update timestamp
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    
    # Write back to file
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        
    return state

def main():
    """
    Main entry point for state update CLI.
    Usage: python update_state.py <artifact_name> <artifact_path> [task_id]
    """
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python update_state.py <artifact_name> <artifact_path> [task_id]")
        sys.exit(1)
        
    artifact_name = sys.argv[1]
    artifact_path = sys.argv[2]
    task_id = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        state = update_state(artifact_name, artifact_path, task_id)
        print(f"State updated successfully for {artifact_name}")
        print(f"Hash: {state['artifact_hashes'][artifact_name]['hash']}")
        print(f"Updated at: {state['updated_at']}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
