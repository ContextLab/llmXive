import json
import os
from pathlib import Path
import logging
from config import ProjectConfig, get_logger

logger = get_logger("state_manager")

def get_state_path(config: ProjectConfig) -> Path:
    """Get the path to the project state YAML file."""
    state_dir = Path("state") / "projects"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / f"{config.project_id}.yaml"

def read_state(config: ProjectConfig) -> dict:
    """Read the current state from the YAML file."""
    state_path = get_state_path(config)
    if not state_path.exists():
        logger.warning(f"State file not found at {state_path}, returning empty state")
        return {}
    
    try:
        import yaml
        with open(state_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Failed to read state file: {str(e)}")
        raise

def write_state(config: ProjectConfig, state: dict) -> None:
    """Write the state to the YAML file."""
    state_path = get_state_path(config)
    try:
        import yaml
        with open(state_path, 'w') as f:
            yaml.dump(state, f, default_flow_style=False)
        logger.info(f"State written to {state_path}")
    except Exception as e:
        logger.error(f"Failed to write state file: {str(e)}")
        raise

def check_bootstrap_flag(config: ProjectConfig) -> bool:
    """Check if bootstrap mode is enabled."""
    state = read_state(config)
    return state.get("bootstrap_mode", False)

def set_bootstrap_flag(config: ProjectConfig, value: bool) -> None:
    """Set the bootstrap mode flag in the state file."""
    state = read_state(config)
    state["bootstrap_mode"] = value
    write_state(config, state)
    logger.info(f"Bootstrap flag set to: {value}")
