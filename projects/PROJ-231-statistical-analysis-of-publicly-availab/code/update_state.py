import os
import hashlib
import yaml
from datetime import datetime
from pathlib import Path
from config import get_project_root, get_data_dir, get_artifacts_dir
import logging

logger = logging.getLogger(__name__)

def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA256 hash of a file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Hex digest of the file hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_directory_hash(dir_path: Path) -> str:
    """
    Compute aggregate hash of all files in a directory.
    
    Args:
        dir_path: Path to the directory
    
    Returns:
        Hex digest of the directory hash
    """
    combined_hash = hashlib.sha256()
    
    if not dir_path.exists():
        logger.warning(f"Directory does not exist: {dir_path}")
        return combined_hash.hexdigest()
        
    # Sort files for deterministic ordering
    files = sorted(dir_path.rglob("*"))
    
    for file_path in files:
        if file_path.is_file() and file_path.suffix not in ['.gitkeep', '.gitignore']:
            combined_hash.update(compute_file_hash(file_path).encode())
            
    return combined_hash.hexdigest()

def load_current_state(project_root: Path) -> dict:
    """
    Load the current state file.
    
    Args:
        project_root: Path to project root
    
    Returns:
        State dictionary
    """
    state_path = project_root / "state.yaml"
    if state_path.exists():
        with open(state_path, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def update_state(project_root: Path) -> dict:
    """
    Update the project state with current artifact hashes.
    
    Args:
        project_root: Path to project root
    
    Returns:
        Updated state dictionary
    """
    state = load_current_state(project_root)
    data_dir = get_data_dir()
    artifacts_dir = get_artifacts_dir()
    
    # Update timestamps
    state['last_updated'] = datetime.now(timezone.utc).isoformat()
    
    # Compute hashes for data directories
    if data_dir.exists():
        state['data_hash'] = compute_directory_hash(data_dir)
        
    if artifacts_dir.exists():
        state['artifacts_hash'] = compute_directory_hash(artifacts_dir)
        
    # Save state
    state_path = project_root / "state.yaml"
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
        
    logger.info(f"Updated project state at {state_path}")
    return state

def main():
    """Main entry point for state update (for testing)."""
    project_root = get_project_root()
    update_state(project_root)
