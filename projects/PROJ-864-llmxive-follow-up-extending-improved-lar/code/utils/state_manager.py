"""
State management for tracking artifact hashes and project state.
"""
import hashlib
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.logging import get_logger, error, info

logger = get_logger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hex digest of the file hash
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        error(f"Failed to hash file {file_path}: {e}")
        return ""

def scan_directory_for_hashes(directory: Path) -> Dict[str, str]:
    """
    Scan a directory and calculate hashes for all files.
    
    Args:
        directory: Path to directory to scan
        
    Returns:
        Dictionary mapping relative paths to their SHA-256 hashes
    """
    hashes = {}
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(directory)
            file_hash = calculate_sha256(file_path)
            if file_hash:
                hashes[str(rel_path)] = file_hash
    return hashes

def load_state_file(state_path: Path) -> Dict[str, Any]:
    """
    Load state file from disk.
    
    Args:
        state_path: Path to state YAML file
        
    Returns:
        State dictionary
    """
    if state_path.exists():
        with open(state_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}

def save_state_file(state_path: Path, state: Dict[str, Any]):
    """
    Save state dictionary to disk.
    
    Args:
        state_path: Path to state YAML file
        state: State dictionary to save
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w") as f:
        yaml.safe_dump(state, f, default_flow_style=False)

def update_project_state(project_root: Path):
    """
    Update the project state file with current artifact hashes.
    
    Args:
        project_root: Path to project root
    """
    state_file = project_root / "state" / f"{project_root.name}.yaml"
    
    # Scan code directory
    code_dir = project_root / "code"
    if code_dir.exists():
        code_hashes = scan_directory_for_hashes(code_dir)
    else:
        code_hashes = {}
    
    # Scan data directory
    data_dir = project_root / "data"
    if data_dir.exists():
        data_hashes = scan_directory_for_hashes(data_dir)
    else:
        data_hashes = {}
    
    # Build state
    state = {
        "project": project_root.name,
        "updated_at": __import__('datetime').datetime.now().isoformat(),
        "artifacts": {
            "code": code_hashes,
            "data": data_hashes
        }
    }
    
    save_state_file(state_file, state)
    info(f"Project state updated at {state_file}")

def main():
    """Main entry point for state management."""
    project_root = Path(__file__).resolve().parent.parent.parent
    update_project_state(project_root)

if __name__ == "__main__":
    main()
