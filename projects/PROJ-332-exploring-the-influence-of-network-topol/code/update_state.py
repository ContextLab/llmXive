"""
Module to update the project state file with artifact hashes.
Implements T038: Calculate SHA-256 of simulation_results.csv and update state YAML.
"""
import os
import hashlib
import yaml
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path

STATE_FILE_PATH = "state/projects/PROJ-332-exploring-the-influence-of-network-topol.yaml"

def calculate_sha256(file_path: str) -> str:
    """
    Calculate the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read file in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state(state_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the state YAML file.
    
    Args:
        state_path: Optional path to state file. Defaults to STATE_FILE_PATH.
        
    Returns:
        Dictionary containing the state data.
    """
    path = state_path or STATE_FILE_PATH
    if not os.path.exists(path):
        # Initialize a new state file if it doesn't exist
        return {
            "project_id": "PROJ-332-exploring-the-influence-of-network-topol",
            "artifact_hashes": {},
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    
    with open(path, "r") as f:
        return yaml.safe_load(f)

def update_state(
    artifact_name: str,
    artifact_path: str,
    task_id: str,
    state_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update the state file with the hash of a new or modified artifact.
    
    Args:
        artifact_name: Name of the artifact (e.g., "simulation_results.csv").
        artifact_path: Path to the artifact file.
        task_id: ID of the task that produced/modified the artifact.
        state_path: Optional path to state file. Defaults to STATE_FILE_PATH.
        
    Returns:
        Updated state dictionary.
        
    Raises:
        FileNotFoundError: If the artifact file does not exist.
    """
    if not os.path.exists(artifact_path):
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
    
    state = load_state(state_path)
    
    # Calculate hash
    file_hash = calculate_sha256(artifact_path)
    
    # Update artifact_hashes
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
        
    state["artifact_hashes"][artifact_name] = {
        "hash": file_hash,
        "task_id": task_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "path": artifact_path
    }
    
    # Update timestamp
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Write back to file
    path = state_path or STATE_FILE_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        
    return state

def main():
    """
    Command-line entry point to update state for a specific artifact.
    Usage: python update_state.py <artifact_path> <artifact_name> <task_id>
    """
    if len(sys.argv) != 4:
        print("Usage: python update_state.py <artifact_path> <artifact_name> <task_id>")
        sys.exit(1)
        
    artifact_path = sys.argv[1]
    artifact_name = sys.argv[2]
    task_id = sys.argv[3]
    
    try:
        state = update_state(artifact_name, artifact_path, task_id)
        print(f"State updated successfully for {artifact_name}")
        print(f"Hash: {state['artifact_hashes'][artifact_name]['hash']}")
    except Exception as e:
        print(f"Error updating state: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
