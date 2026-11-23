import hashlib
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from src.utils.config import get_path

def compute_file_checksum(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum
        
    Returns:
        Hexadecimal string of the SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def compute_directory_checksum(dir_path: Path) -> Dict[str, str]:
    """
    Computes checksums for all files in a directory recursively.
    
    Args:
        dir_path: Path to the directory to checksum
        
    Returns:
        Dictionary mapping relative file paths to their checksums
    """
    checksums = {}
    if not dir_path.exists():
        return checksums
        
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(dir_path)
            checksums[str(rel_path)] = compute_file_checksum(file_path)
            
    return checksums

def ensure_state_dir() -> Path:
    """
    Ensures the state directory exists and returns its path.
    
    Returns:
        Path to the state directory
    """
    state_dir = get_path("state/projects")
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir

def load_state(project_id: str = "PROJ-369-evaluating-the-robustness-of-statistical") -> Optional[Dict[str, Any]]:
    """
    Loads the state file for a project.
    
    Args:
        project_id: The project identifier
        
    Returns:
        Dictionary containing the project state, or None if file doesn't exist
    """
    state_file = ensure_state_dir() / f"{project_id}.yaml"
    if not state_file.exists():
        return None
        
    with open(state_file, "r") as f:
        return yaml.safe_load(f)

def save_state(state: Dict[str, Any], project_id: str = "PROJ-369-evaluating-the-robustness-of-statistical") -> None:
    """
    Saves the state file for a project.
    
    Args:
        state: Dictionary containing the project state
        project_id: The project identifier
    """
    state_file = ensure_state_dir() / f"{project_id}.yaml"
    with open(state_file, "w") as f:
        yaml.safe_dump(state, f, default_flow_style=False, sort_keys=False)

def update_checksums_for_project(project_id: str = "PROJ-369-evaluating-the-robustness-of-statistical") -> None:
    """
    Computes checksums for key data directories and updates the project state.
    This satisfies Constitution Principle III and V.
    
    Args:
        project_id: The project identifier
    """
    # Load existing state or create new
    state = load_state(project_id)
    if state is None:
        state = {
            "project_id": project_id,
            "last_updated": None,
            "checksums": {}
        }
    
    # Define directories to checksum
    dirs_to_checksum = [
        "data/raw",
        "data/processed",
        "results"
    ]
    
    # Compute checksums for each directory
    for dir_name in dirs_to_checksum:
        dir_path = get_path(dir_name)
        if dir_path.exists():
          dir_checksums = compute_directory_checksum(dir_path)
          state["checksums"][dir_name] = dir_checksums
          state["last_updated"] = str(dir_path.stat().st_mtime) if any(dir_path.iterdir()) else None
        else:
            state["checksums"][dir_name] = {}
    
    # Save updated state
    save_state(state, project_id)
    print(f"Updated checksums for project {project_id}")

def validate_checksums_for_project(project_id: str = "PROJ-369-evaluating-the-robustness-of-statistical") -> bool:
    """
    Validates that current directory checksums match the stored state.
    
    Args:
        project_id: The project identifier
        
    Returns:
        True if all checksums match, False otherwise
    """
    state = load_state(project_id)
    if state is None:
        print(f"No state file found for project {project_id}")
        return False
    
    # Define directories to validate
    dirs_to_validate = [
        "data/raw",
        "data/processed",
        "results"
    ]
    
    all_valid = True
    for dir_name in dirs_to_validate:
        dir_path = get_path(dir_name)
        if not dir_path.exists():
            print(f"Directory {dir_name} does not exist")
            all_valid = False
            continue
            
        current_checksums = compute_directory_checksum(dir_path)
        stored_checksums = state["checksums"].get(dir_name, {})
        
        if current_checksums != stored_checksums:
            print(f"Checksum mismatch for {dir_name}")
            # Detailed diff for debugging
            all_files = set(current_checksums.keys()) | set(stored_checksums.keys())
            for file_name in all_files:
                current_val = current_checksums.get(file_name, "MISSING")
                stored_val = stored_checksums.get(file_name, "MISSING")
                if current_val != stored_val:
                    print(f"  {file_name}: {current_val} != {stored_val}")
            all_valid = False
        else:
            print(f"Checksums valid for {dir_name}")
            
    return all_valid
