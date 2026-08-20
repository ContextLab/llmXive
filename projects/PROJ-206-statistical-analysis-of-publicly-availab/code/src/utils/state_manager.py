"""
State management utility for the llmXive pipeline.

This module provides functions to compute SHA-256 hashes for artifacts,
manage the state YAML file, and update artifact records upon creation.
"""
import hashlib
import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.utils.config import get_state_root, get_project_root

# Project identifier derived from the task context
PROJECT_ID = "PROJ-206-statistical-analysis-of-publicly-availab"

def compute_file_hash(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files efficiently
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_state_file_path() -> Path:
    """
    Get the path to the project's state YAML file.
    
    Returns:
        Path to the state file (state/projects/PROJ-206-*.yaml).
    """
    state_root = get_state_root()
    state_root.mkdir(parents=True, exist_ok=True)
    return state_root / f"{PROJECT_ID}.yaml"

def load_state() -> Dict[str, Any]:
    """
    Load the current state from the YAML file.
    
    Returns:
        Dictionary containing the state data.
        Returns an empty structure if the file does not exist.
    """
    state_path = get_state_file_path()
    if not state_path.exists():
        return {
            "project_id": PROJECT_ID,
            "created_at": datetime.utcnow().isoformat(),
            "artifacts": {}
        }
    
    with open(state_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        if data is None:
            return {
                "project_id": PROJECT_ID,
                "created_at": datetime.utcnow().isoformat(),
                "artifacts": {}
            }
        return data

def update_state_artifact(
    artifact_name: str, 
    artifact_path: str, 
    description: Optional[str] = None
) -> None:
    """
    Update the state file with a new or updated artifact record.
    
    Computes the SHA-256 hash of the artifact and records metadata.
    
    Args:
        artifact_name: Unique name for the artifact (e.g., 'poll_data_cleaned').
        artifact_path: Relative or absolute path to the artifact file.
        description: Optional description of the artifact.
        
    Raises:
        FileNotFoundError: If the artifact file does not exist.
    """
    path_obj = Path(artifact_path)
    if not path_obj.is_absolute():
        # Resolve relative to project root if not absolute
        project_root = get_project_root()
        path_obj = project_root / artifact_path
        
    if not path_obj.exists():
        raise FileNotFoundError(f"Artifact file not found: {path_obj}")

    file_hash = compute_file_hash(path_obj)
    state = load_state()
    
    # Ensure artifacts key exists
    if "artifacts" not in state:
        state["artifacts"] = {}
        
    # Update artifact record
    state["artifacts"][artifact_name] = {
        "path": str(path_obj.relative_to(get_project_root())),
        "hash": file_hash,
        "updated_at": datetime.utcnow().isoformat(),
        "description": description or f"Derived artifact: {artifact_name}"
    }
    
    # Write back to file
    with open(get_state_file_path(), "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def verify_artifact_integrity(artifact_name: str) -> bool:
    """
    Verify the integrity of an artifact by comparing its current hash
    with the hash stored in the state file.
    
    Args:
        artifact_name: Name of the artifact to verify.
        
    Returns:
        True if the artifact exists and hash matches, False otherwise.
    """
    state = load_state()
    if "artifacts" not in state or artifact_name not in state["artifacts"]:
        return False
        
    recorded_hash = state["artifacts"][artifact_name].get("hash")
    artifact_path_str = state["artifacts"][artifact_name].get("path")
    
    if not artifact_path_str:
        return False
        
    path_obj = get_project_root() / artifact_path_str
    if not path_obj.exists():
        return False
        
    current_hash = compute_file_hash(path_obj)
    return current_hash == recorded_hash

def main() -> None:
    """
    CLI entry point for state management utilities.
    
    Usage:
        python -m src.utils.state_manager --action <action> [args]
        
    Actions:
        update: Update state for a specific artifact
        verify: Verify integrity of a specific artifact
        status: Print current state summary
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="State Management Utility")
    parser.add_argument("--action", choices=["update", "verify", "status"], required=True)
    parser.add_argument("--artifact", help="Artifact name/path for update/verify")
    parser.add_argument("--description", help="Description for update action")
    
    args = parser.parse_args()
    
    if args.action == "update":
        if not args.artifact:
            parser.error("--artifact is required for update action")
        print(f"Updating state for artifact: {args.artifact}")
        try:
            update_state_artifact(args.artifact, args.artifact, args.description)
            print("State updated successfully.")
        except FileNotFoundError as e:
            print(f"Error: {e}")
            exit(1)
            
    elif args.action == "verify":
        if not args.artifact:
            parser.error("--artifact is required for verify action")
        print(f"Verifying integrity for artifact: {args.artifact}")
        is_valid = verify_artifact_integrity(args.artifact)
        if is_valid:
            print("Integrity check PASSED.")
        else:
            print("Integrity check FAILED.")
            exit(1)
            
    elif args.action == "status":
        state = load_state()
        print(f"Project State: {state.get('project_id')}")
        print(f"Created: {state.get('created_at')}")
        print(f"Artifacts recorded: {len(state.get('artifacts', {}))}")
        for name, details in state.get("artifacts", {}).items():
            print(f"  - {name}: {details.get('hash', 'N/A')[:16]}...")

if __name__ == "__main__":
    main()
