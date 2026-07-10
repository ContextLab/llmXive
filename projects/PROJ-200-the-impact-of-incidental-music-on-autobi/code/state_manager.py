"""
State Manager for llmXive pipeline.

Handles checksum tracking of derived files in state.yaml.
Ensures reproducibility by verifying data integrity across pipeline runs.
"""
import os
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from config import get_project_root
from utils import get_logger

logger = get_logger(__name__)

STATE_FILE_PATH = "state.yaml"

def _get_state_file_path() -> Path:
    """Get the absolute path to the state.yaml file."""
    return get_project_root() / STATE_FILE_PATH

def _calculate_file_checksum(file_path: Path) -> str:
    """
    Calculate SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot calculate checksum: file not found at {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def load_state() -> Dict[str, Any]:
    """
    Load the state.yaml file.
    
    Returns:
        Dictionary containing the state. Returns empty structure if file doesn't exist.
    """
    state_path = _get_state_file_path()
    if not state_path.exists():
        logger.info("State file not found. Initializing empty state.")
        return {
            "version": "1.0",
            "last_updated": None,
            "files": {}
        }
    
    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f)
            if state is None:
                return {"version": "1.0", "last_updated": None, "files": {}}
            return state
    except yaml.YAMLError as e:
        logger.error(f"Error parsing state.yaml: {e}")
        raise

def save_state(state: Dict[str, Any]) -> None:
    """
    Save the state dictionary to state.yaml.
    
    Args:
        state: The state dictionary to save.
    """
    state_path = _get_state_file_path()
    state["last_updated"] = datetime.utcnow().isoformat()
    
    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"State saved to {state_path}")

def register_file(file_path: Path, description: Optional[str] = None) -> None:
    """
    Register a derived file in the state, calculating and storing its checksum.
    
    Args:
        file_path: Path to the derived file.
        description: Optional human-readable description of the file.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot register file: {file_path} does not exist.")
    
    state = load_state()
    relative_path = str(file_path.relative_to(get_project_root()))
    
    checksum = _calculate_file_checksum(file_path)
    
    state["files"][relative_path] = {
        "checksum": checksum,
        "size_bytes": file_path.stat().st_size,
        "description": description or "Auto-registered derived file",
        "registered_at": datetime.utcnow().isoformat()
    }
    
    save_state(state)
    logger.info(f"Registered file: {relative_path} (checksum: {checksum[:16]}...)")

def verify_file(file_path: Path) -> bool:
    """
    Verify a derived file against its stored checksum in state.yaml.
    
    Args:
        file_path: Path to the file to verify.
        
    Returns:
        True if the file exists and checksum matches, False otherwise.
    """
    state = load_state()
    relative_path = str(file_path.relative_to(get_project_root()))
    
    if relative_path not in state.get("files", {}):
        logger.warning(f"File not registered in state: {relative_path}")
        return False
    
    stored_checksum = state["files"][relative_path]["checksum"]
    
    if not file_path.exists():
        logger.error(f"File missing but registered in state: {relative_path}")
        return False
    
    current_checksum = _calculate_file_checksum(file_path)
    
    if current_checksum != stored_checksum:
        logger.error(
            f"Checksum mismatch for {relative_path}.\n"
            f"  Stored:   {stored_checksum}\n"
            f"  Current:  {current_checksum}"
        )
        return False
    
    logger.info(f"Verification passed for {relative_path}")
    return True

def verify_all() -> bool:
    """
    Verify all registered files against their stored checksums.
    
    Returns:
        True if all files pass verification, False otherwise.
    """
    state = load_state()
    all_valid = True
    
    for relative_path, metadata in state.get("files", {}).items():
        file_path = get_project_root() / relative_path
        if not verify_file(file_path):
            all_valid = False
    
    if all_valid:
        logger.info("All registered files verified successfully.")
    else:
        logger.warning("Some files failed verification.")
    
    return all_valid

def get_file_info(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Get metadata for a registered file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Dictionary with file metadata if registered, None otherwise.
    """
    state = load_state()
    relative_path = str(file_path.relative_to(get_project_root()))
    
    return state.get("files", {}).get(relative_path)

def clear_stale_entries(threshold_days: int = 30) -> int:
    """
    Remove entries from state.yaml that haven't been accessed/verified in a while.
    
    Args:
        threshold_days: Number of days after which an entry is considered stale.
        
    Returns:
        Number of entries removed.
    """
    state = load_state()
    now = datetime.utcnow()
    removed_count = 0
    
    files_to_keep = {}
    for path, metadata in state.get("files", {}).items():
        # For simplicity, we check registered_at. In a more complex system,
        # we might track last_verified_at.
        reg_time_str = metadata.get("registered_at")
        if reg_time_str:
            try:
                reg_time = datetime.fromisoformat(reg_time_str)
                if (now - reg_time).days < threshold_days:
                    files_to_keep[path] = metadata
                else:
                    removed_count += 1
            except ValueError:
                # Keep if we can't parse the date
                files_to_keep[path] = metadata
        else:
            # Keep if no timestamp
            files_to_keep[path] = metadata
    
    if removed_count > 0:
        state["files"] = files_to_keep
        save_state(state)
        logger.info(f"Removed {removed_count} stale entries from state.")
    
    return removed_count
