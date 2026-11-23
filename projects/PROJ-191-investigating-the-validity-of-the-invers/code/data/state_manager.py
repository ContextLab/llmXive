import json
import os
from pathlib import Path
import logging
from config import ProjectConfig, get_logger

logger = get_logger("state_manager")

def get_state_path():
    """Returns the path to the state YAML file."""
    # The task description mentions state/projects/PROJ-191...yaml
    # But the project root is projects/PROJ-191...
    # We will place it in the project root's 'state' directory as per standard conventions
    # or relative to the code directory if that's where the project lives.
    # Given the task says "state/projects/PROJ-191...yaml", let's assume the root is the repo root.
    # We'll use a relative path from the current working directory.
    return Path("state/projects/PROJ-191-investigating-the-validity-of-the-invers.yaml")

def read_state():
    """Reads the state file and returns a dictionary."""
    state_path = get_state_path()
    if not state_path.exists():
        logger.warning(f"State file not found at {state_path}. Returning empty state.")
        return {}
    try:
        import yaml
        with open(state_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to read state file: {e}")
        return {}

def write_state(state: dict):
    """Writes the state dictionary to the state file."""
    state_path = get_state_path()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import yaml
        with open(state_path, 'w') as f:
            yaml.dump(state, f)
        logger.info(f"State file written to {state_path}")
    except Exception as e:
        logger.error(f"Failed to write state file: {e}")
        raise

def check_bootstrap_flag():
    """Checks if the bootstrap flag is set in the state."""
    state = read_state()
    return state.get("bootstrap_needed", False)

def set_bootstrap_flag(flag: bool):
    """Sets the bootstrap flag in the state."""
    state = read_state()
    state["bootstrap_needed"] = flag
    write_state(state)
    logger.info(f"Bootstrap flag set to {flag}")
