"""
State management module for artifact hashing and project state tracking.

This module handles:
- Computing SHA-256 hashes for files
- Scanning directories for artifacts
- Loading and saving project state YAML files
- Updating artifact hashes in the project state
- Verifying artifact integrity against stored hashes
"""
import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Project root is assumed to be the parent of the code directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE = STATE_DIR / "PROJ-006-agriculture-optimization.yaml"

# Directories to scan for artifacts
DATA_DIRS = [
    PROJECT_ROOT / "data" / "raw",
    PROJECT_ROOT / "data" / "processed",
]

def compute_file_hash(file_path: Path) -> Optional[str]:
    """
    Compute SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hex digest string or None if file doesn't exist
    """
    if not file_path.exists():
        logger.warning(f"File does not exist: {file_path}")
        return None
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        return None

def scan_directory_for_artifacts(directory: Path) -> Dict[str, str]:
    """
    Scan a directory recursively and compute hashes for all files.
    
    Args:
        directory: Path to directory to scan
        
    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes
    """
    artifacts = {}
    
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return artifacts
    
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            relative_path = file_path.relative_to(PROJECT_ROOT)
            file_hash = compute_file_hash(file_path)
            if file_hash:
                artifacts[str(relative_path)] = file_hash
    
    return artifacts

def load_state() -> Dict[str, Any]:
    """
    Load the project state YAML file.
    
    Returns:
        Dictionary containing project state, or empty dict if file doesn't exist
    """
    if not STATE_FILE.exists():
        logger.info(f"State file does not exist yet: {STATE_FILE}")
        return {
            "project_id": "PROJ-006-agriculture-optimization",
            "last_updated": None,
            "artifact_hashes": {}
        }
    
    try:
        with open(STATE_FILE, "r") as f:
            state = yaml.safe_load(f)
            return state if state else {}
    except Exception as e:
        logger.error(f"Error loading state file: {e}")
        return {}

def save_state(state: Dict[str, Any]) -> bool:
    """
    Save the project state to the YAML file.
    
    Args:
        state: Dictionary containing project state
        
    Returns:
        True if successful, False otherwise
    """
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATE_FILE, "w") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State saved to {STATE_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving state file: {e}")
        return False

def update_artifact_hashes() -> Dict[str, str]:
    """
    Scan data directories and update artifact hashes in the project state.
    
    Returns:
        Dictionary of updated artifact hashes
    """
    all_artifacts = {}
    
    for data_dir in DATA_DIRS:
        if data_dir.exists():
          logger.info(f"Scanning directory: {data_dir}")
          artifacts = scan_directory_for_artifacts(data_dir)
          all_artifacts.update(artifacts)
        else:
            logger.warning(f"Data directory does not exist: {data_dir}")
    
    # Load existing state
    state = load_state()
    
    # Update artifact hashes
    state["artifact_hashes"] = all_artifacts
    state["last_updated"] = str(Path(__file__).resolve())
    
    # Save updated state
    save_state(state)
    
    return all_artifacts

def verify_artifacts() -> bool:
    """
    Verify that all artifacts in the state file match their stored hashes.
    
    Returns:
        True if all artifacts match, False otherwise
    """
    state = load_state()
    stored_hashes = state.get("artifact_hashes", {})
    
    if not stored_hashes:
        logger.warning("No artifact hashes found in state file")
        return False
    
    all_match = True
    for relative_path, expected_hash in stored_hashes.items():
        file_path = PROJECT_ROOT / relative_path
        
        if not file_path.exists():
            logger.error(f"Artifact missing: {file_path}")
            all_match = False
            continue
        
        actual_hash = compute_file_hash(file_path)
        
        if actual_hash != expected_hash:
            logger.error(f"Hash mismatch for {file_path}: expected {expected_hash}, got {actual_hash}")
            all_match = False
        else:
            logger.info(f"Verified: {file_path}")
    
    return all_match

def main():
    """
    Main entry point for state management CLI operations.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage project state and artifact hashes")
    parser.add_argument(
        "command",
        choices=["update", "verify", "show"],
        help="Command to execute"
    )
    
    args = parser.parse_args()
    
    if args.command == "update":
        logger.info("Updating artifact hashes...")
        hashes = update_artifact_hashes()
        logger.info(f"Updated {len(hashes)} artifact hashes")
        for path, hash_val in hashes.items():
            logger.info(f"  {path}: {hash_val[:16]}...")
            
    elif args.command == "verify":
        logger.info("Verifying artifacts...")
        if verify_artifacts():
            logger.info("All artifacts verified successfully")
        else:
            logger.error("Verification failed - some artifacts do not match")
            
    elif args.command == "show":
        state = load_state()
        logger.info(f"Project State: {STATE_FILE}")
        logger.info(f"Project ID: {state.get('project_id', 'Unknown')}")
        logger.info(f"Last Updated: {state.get('last_updated', 'Never')}")
        logger.info(f"Artifact Count: {len(state.get('artifact_hashes', {}))}")
        for path, hash_val in state.get("artifact_hashes", {}).items():
            logger.info(f"  {path}: {hash_val}")

if __name__ == "__main__":
    main()
