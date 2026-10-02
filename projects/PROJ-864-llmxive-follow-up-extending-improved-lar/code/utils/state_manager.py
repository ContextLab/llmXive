"""
State Manager for llmXive project.
Computes SHA-256 hashes of all files under code/ and data/ directories
and updates the project state file.
"""
import hashlib
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.logging import get_logger, error, info

logger = get_logger(__name__)

def get_project_root() -> Path:
    """Returns the root directory of the current project."""
    # Assuming the project root is the parent of the 'code' directory
    # This script is located at code/utils/state_manager.py
    return Path(__file__).resolve().parent.parent.parent

def get_state_dir() -> Path:
    """Returns the path to the state directory."""
    return get_project_root() / "state"

def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to hash file {file_path}: {e}")
        raise

def scan_directory_for_hashes(directory: Path) -> Dict[str, str]:
    """
    Recursively scan a directory and compute hashes for all files.

    Args:
        directory: Root directory to scan.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    hashes = {}
    if not directory.exists():
        logger.warning(f"Directory {directory} does not exist, skipping.")
        return hashes

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            # Skip state files themselves to avoid circular dependency
            if "state" in str(file_path):
                continue
            
            relative_path = file_path.relative_to(get_project_root())
            try:
                file_hash = calculate_sha256(file_path)
                hashes[str(relative_path)] = file_hash
                logger.debug(f"Hashed {relative_path}: {file_hash[:8]}...")
            except Exception as e:
                logger.error(f"Skipping file {relative_path} due to error: {e}")
    
    return hashes

def load_state_file(state_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the existing state file or return an empty structure.

    Args:
        state_path: Optional path to the state file. Defaults to project state file.

    Returns:
        Dictionary representing the state file contents.
    """
    if state_path is None:
        state_path = get_state_dir() / "projects" / "PROJ-864-llmxive-follow-up-extending-improved-lar.yaml"
    
    if not state_path.exists():
        logger.info(f"State file {state_path} not found. Initializing new state.")
        return {
            "project_id": "PROJ-864-llmxive-follow-up-extending-improved-lar",
            "last_updated": None,
            "artifact_hashes": {}
        }
    
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse state file {state_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to load state file {state_path}: {e}")
        raise

def save_state_file(state_data: Dict[str, Any], state_path: Optional[Path] = None) -> None:
    """
    Save the state dictionary to the state file.

    Args:
        state_data: Dictionary to save.
        state_path: Optional path to the state file.
    """
    if state_path is None:
        state_path = get_state_dir() / "projects" / "PROJ-864-llmxive-follow-up-extending-improved-lar.yaml"
    
    # Ensure directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State saved to {state_path}")
    except Exception as e:
        logger.error(f"Failed to save state file {state_path}: {e}")
        raise

def get_artifact_hash(relative_path: str) -> Optional[str]:
    """
    Get the hash for a specific artifact if it exists in the current state.
    
    Args:
        relative_path: Relative path to the artifact.
        
    Returns:
        Hash string or None if not found.
    """
    state = load_state_file()
    return state.get("artifact_hashes", {}).get(relative_path)

def update_project_state() -> Dict[str, Any]:
    """
    Main entry point to update the project state.
    Scans code/ and data/ directories, computes hashes, and saves to state file.

    Returns:
        Updated state dictionary.
    """
    logger.info("Starting state update for project...")
    
    # Directories to scan
    dirs_to_scan = [
        get_project_root() / "code",
        get_project_root() / "data"
    ]
    
    all_hashes: Dict[str, str] = {}
    
    for directory in dirs_to_scan:
        if directory.exists():
            logger.info(f"Scanning directory: {directory}")
            dir_hashes = scan_directory_for_hashes(directory)
            all_hashes.update(dir_hashes)
        else:
            logger.warning(f"Directory {directory} not found, skipping.")
    
    # Load existing state
    state = load_state_file()
    
    # Update state
    import datetime
    state["last_updated"] = datetime.datetime.now().isoformat()
    state["artifact_hashes"] = all_hashes
    
    # Save state
    save_state_file(state)
    
    logger.info(f"State update complete. Total artifacts tracked: {len(all_hashes)}")
    return state

def main() -> int:
    """
    Command-line entry point for the state manager.
    
    Returns:
        0 on success, 1 on failure.
    """
    try:
        update_project_state()
        return 0
    except Exception as e:
        error(f"State manager failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
