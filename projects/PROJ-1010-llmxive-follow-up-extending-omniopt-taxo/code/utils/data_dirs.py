"""
Utility module for managing data directory structures and state tracking.
"""
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from utils.logging import get_logger, info, error, warning

logger = get_logger(__name__)

def ensure_dir(path: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Absolute or relative path to the directory
    """
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        info(f"Created directory: {path}")
    else:
        debug(f"Directory already exists: {path}")

def setup_base_data_structure(base_path: str) -> None:
    """
    Create the base data directory structure required for the project.
    
    Creates:
        - data/raw/
        - data/processed/
        - data/figures/
        - data/omniopt_lookup.json (initial empty structure)
    
    Args:
        base_path: Root path for the data directory
    """
    data_path = os.path.join(base_path, "data")
    raw_path = os.path.join(data_path, "raw")
    processed_path = os.path.join(data_path, "processed")
    figures_path = os.path.join(data_path, "figures")
    
    # Create directories
    ensure_dir(raw_path)
    ensure_dir(processed_path)
    ensure_dir(figures_path)
    
    info(f"Base data structure created at: {data_path}")
    
    # Initialize OmniOpt lookup file if it doesn't exist
    lookup_path = os.path.join(data_path, "omniopt_lookup.json")
    if not os.path.exists(lookup_path):
        create_omniopt_lookup(lookup_path)
    else:
        info(f"OmniOpt lookup file already exists: {lookup_path}")

def get_state(state_path: str) -> Dict[str, Any]:
    """
    Load the current state from a JSON file.
    
    Args:
        state_path: Path to the state JSON file
        
    Returns:
        Dictionary containing the current state, or empty dict if file doesn't exist
    """
    if not os.path.exists(state_path):
        return {}
    
    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        error(f"Failed to read state file {state_path}: {e}")
        return {}

def update_state(state_path: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the state file with new values, merging with existing state.
    
    Args:
        state_path: Path to the state JSON file
        updates: Dictionary of key-value pairs to update
        
    Returns:
        The updated state dictionary
    """
    current_state = get_state(state_path)
    current_state.update(updates)
    
    # Ensure parent directory exists
    parent_dir = os.path.dirname(state_path)
    if parent_dir:
        ensure_dir(parent_dir)
    
    try:
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(current_state, f, indent=2, default=str)
        info(f"State updated successfully: {state_path}")
    except IOError as e:
        error(f"Failed to write state file {state_path}: {e}")
        raise
    
    return current_state

def create_omniopt_lookup(lookup_path: str) -> None:
    """
    Create an initial OmniOpt lookup JSON file with an empty structure.
    
    The file will contain a version field and an empty models dictionary.
    This serves as the template for populating with real benchmark data later.
    
    Args:
        lookup_path: Path where the lookup file should be created
    """
    initial_structure = {
        "version": "1.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": "OmniOpt benchmark results lookup table",
        "models": {}
    }
    
    try:
        with open(lookup_path, 'w', encoding='utf-8') as f:
            json.dump(initial_structure, f, indent=2)
        info(f"Created OmniOpt lookup template: {lookup_path}")
    except IOError as e:
        error(f"Failed to create OmniOpt lookup file: {e}")
        raise

def main() -> None:
    """
    Main entry point for setting up data directories when run as a script.
    
    Usage: python -m utils.data_dirs
    """
    # Determine base path (project root)
    # Assuming this script is run from the code/ directory
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    logger.info(f"Setting up data directories for project at: {base_path}")
    setup_base_data_structure(base_path)
    
    # Initialize state tracking file
    state_path = os.path.join(base_path, "state", "pipeline_state.json")
    if not os.path.exists(state_path):
        update_state(state_path, {
            "project_id": "PROJ-1010-llmxive-follow-up-extending-omniopt-taxo",
            "setup_complete": True,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    else:
        update_state(state_path, {
            "last_data_setup": datetime.now(timezone.utc).isoformat()
        })
    
    logger.info("Data directory setup complete.")

if __name__ == "__main__":
    main()
