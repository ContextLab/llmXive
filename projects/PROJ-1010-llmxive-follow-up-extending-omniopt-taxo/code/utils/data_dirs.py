"""
Data directory management and state tracking for the llmXive pipeline.

This module handles the creation of the required base data directory structure
and initializes the state tracking file.
"""
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Import existing utilities
from utils.logging import get_logger, info, error, warning

logger = get_logger(__name__)

# Base directory relative to project root
BASE_DATA_DIR = "data"

# Required subdirectories
REQUIRED_DIRS = [
    "raw",
    "processed",
    "figures",
    "cache",
]

# State tracking file name
STATE_FILE_NAME = "state.json"


def ensure_dir(directory_path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory_path: Path to the directory (relative or absolute).
        
    Returns:
        True if the directory exists or was created successfully, False otherwise.
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)
            logger.debug(f"Created directory: {directory_path}")
        return True
    except OSError as e:
        logger.error(f"Failed to create directory {directory_path}: {e}")
        return False


def setup_base_data_structure(base_path: Optional[str] = None) -> Dict[str, str]:
    """
    Create the base data directory structure required by the pipeline.
    
    Creates:
        - data/raw/
        - data/processed/
        - data/figures/
        - data/cache/
        - data/state.json (initialization)
    
    Args:
        base_path: Optional base path. If None, uses BASE_DATA_DIR relative to CWD.
        
    Returns:
        Dictionary mapping logical names to absolute paths.
        
    Raises:
        RuntimeError: If directory creation fails.
    """
    base = base_path if base_path else BASE_DATA_DIR
    
    # Ensure base directory exists
    if not ensure_dir(base):
        raise RuntimeError(f"Failed to create base data directory: {base}")
    
    paths = {}
    for subdir in REQUIRED_DIRS:
        full_path = os.path.join(base, subdir)
        if not ensure_dir(full_path):
            raise RuntimeError(f"Failed to create subdirectory: {full_path}")
        paths[subdir] = full_path
    
    # Initialize state file
    state_path = os.path.join(base, STATE_FILE_NAME)
    if not os.path.exists(state_path):
        init_state = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_modified": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
            "status": "initialized",
            "datasets": {},
            "processing_runs": []
        }
        try:
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(init_state, f, indent=2)
            logger.info(f"Initialized state file: {state_path}")
        except IOError as e:
            raise RuntimeError(f"Failed to create state file {state_path}: {e}")
    
    paths["state"] = state_path
    logger.info(f"Base data structure created at: {base}")
    return paths


def get_state(base_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the current state from the state file.
    
    Args:
        base_path: Optional base path. If None, uses BASE_DATA_DIR.
        
    Returns:
        Dictionary containing the state data.
        
    Raises:
        FileNotFoundError: If state file does not exist.
        json.JSONDecodeError: If state file is corrupted.
    """
    base = base_path if base_path else BASE_DATA_DIR
    state_path = os.path.join(base, STATE_FILE_NAME)
    
    if not os.path.exists(state_path):
        raise FileNotFoundError(f"State file not found: {state_path}")
    
    with open(state_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def update_state(base_path: Optional[str] = None, updates: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Update the state file with new data.
    
    Args:
        base_path: Optional base path. If None, uses BASE_DATA_DIR.
        updates: Dictionary of key-value pairs to update in the state.
        
    Returns:
        The updated state dictionary.
        
    Raises:
        FileNotFoundError: If state file does not exist.
        IOError: If file cannot be written.
    """
    state = get_state(base_path)
    
    if updates:
        state.update(updates)
    
    state["last_modified"] = datetime.now(timezone.utc).isoformat()
    
    base = base_path if base_path else BASE_DATA_DIR
    state_path = os.path.join(base, STATE_FILE_NAME)
    
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)
    
    return state


def create_omniopt_lookup(base_path: Optional[str] = None) -> str:
    """
    Create an empty OmniOpt lookup table if it doesn't exist.
    
    Args:
        base_path: Optional base path. If None, uses BASE_DATA_DIR.
        
    Returns:
        Path to the created lookup file.
    """
    base = base_path if base_path else BASE_DATA_DIR
    lookup_path = os.path.join(base, "omniopt_lookup.json")
    
    if not os.path.exists(lookup_path):
        initial_lookup = {
            "version": "1.0.0",
            "source": "OmniOpt Benchmark",
            "entries": {},
            "metadata": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "description": "Mapping of model architectures to optimal optimizer families"
            }
        }
        with open(lookup_path, 'w', encoding='utf-8') as f:
            json.dump(initial_lookup, f, indent=2)
        logger.info(f"Created empty OmniOpt lookup table: {lookup_path}")
    else:
        logger.info(f"OmniOpt lookup table already exists: {lookup_path}")
        
    return lookup_path


def main():
    """
    CLI entry point to set up the data directory structure.
    """
    logger.info("Starting data directory setup...")
    
    try:
        paths = setup_base_data_structure()
        lookup_path = create_omniopt_lookup()
        
        info("Data directory structure created successfully:")
        for name, path in paths.items():
            if name != "state":
                info(f"  - {name}: {path}")
        info(f"  - state file: {paths['state']}")
        info(f"  - OmniOpt lookup: {lookup_path}")
        
    except RuntimeError as e:
        error(f"Setup failed: {e}")
        raise


if __name__ == "__main__":
    main()
