"""
Utility module for managing runtime state files (state.json).
This is a helper to ensure T016 and T030 can interact with the state file cleanly.
"""
import json
import os
from pathlib import Path
import logging
from config import ProjectConfig, get_logger

logger = get_logger(__name__)

def get_state_path() -> Path:
    """Return the path to the state.json file."""
    config = ProjectConfig()
    return Path(config.data_dir) / "processed" / "state.json"

def read_state() -> dict:
    """Read the current state from state.json."""
    state_path = get_state_path()
    if not state_path.exists():
        return {}
    try:
        with open(state_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to read state file: {e}")
        return {}

def write_state(state: dict) -> None:
    """Write the state to state.json atomically."""
    state_path = get_state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    temp_path = state_path.with_suffix('.tmp')
    with open(temp_path, 'w') as f:
        json.dump(state, f, indent=2)
    
    os.replace(temp_path, state_path)
    logger.info(f"State written to {state_path}")

def check_bootstrap_flag() -> bool:
    """
    Check if USE_BOOTSTRAP flag is set in state.json.
    Returns True if USE_BOOTSTRAP is True, False otherwise.
    """
    state = read_state()
    return state.get('USE_BOOTSTRAP', False)

def set_bootstrap_flag(flag: bool) -> None:
    """
    Set the USE_BOOTSTRAP flag in state.json.
    This is a convenience wrapper for T016.
    """
    state = read_state()
    state['USE_BOOTSTRAP'] = flag
    # Also update detected_runs if available in current context, 
    # but this function is mainly for toggling the flag.
    write_state(state)