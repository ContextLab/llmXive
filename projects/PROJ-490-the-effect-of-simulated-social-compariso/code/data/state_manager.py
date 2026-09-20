"""
State management utilities for the llmXive automated science pipeline.
Handles reading, updating, and persisting project state YAML files.
"""
import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

from data.config import get_config
from utils.logger import get_logger

logger = get_logger(__name__)


def load_state_file(state_path: Path) -> Dict[str, Any]:
    """
    Load a state YAML file. Returns an empty dict if the file does not exist.

    Args:
        state_path: Path to the state YAML file.

    Returns:
        Dictionary containing the state contents.
    """
    if not state_path.exists():
        logger.info(f"State file not found at {state_path}. Initializing empty state.")
        return {}

    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
            return content if content else {}
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse state file {state_path}: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to read state file {state_path}: {e}")
        raise


def save_state_file(state_path: Path, state_dict: Dict[str, Any]) -> None:
    """
    Save a dictionary to a state YAML file, creating parent directories if needed.

    Args:
        state_path: Path to the state YAML file.
        state_dict: Dictionary to save.
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(state_path, 'w', encoding='utf-8') as f:
            yaml.dump(state_dict, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State file saved to {state_path}")
    except Exception as e:
        logger.error(f"Failed to write state file {state_path}: {e}")
        raise


def update_project_state(project_id: str, updates: Dict[str, Any]) -> None:
    """
    Update the project-specific state file with new key-value pairs.
    Merges updates into the existing state.

    Args:
        project_id: The project identifier (e.g., 'PROJ-490-the-effect-of-simulated-social-compariso').
        updates: Dictionary of keys and values to update in the state.
    """
    config = get_config()
    state_dir = Path(config['state_dir'])
    state_file = state_dir / f"{project_id}.yaml"

    current_state = load_state_file(state_file)
    current_state.update(updates)

    save_state_file(state_file, current_state)


def update_data_source_type(project_id: str, source_type: str) -> None:
    """
    Update the data_source_type field in the project state.
    Valid values: 'real', 'synthetic'.

    Args:
        project_id: The project identifier.
        source_type: The data source type ('real' or 'synthetic').
    """
    if source_type not in ('real', 'synthetic'):
        raise ValueError(f"Invalid data_source_type: {source_type}. Must be 'real' or 'synthetic'.")

    logger.info(f"Updating data_source_type to '{source_type}' for project {project_id}")
    update_project_state(project_id, {'data_source_type': source_type})


def main() -> None:
    """
    Entry point for the state manager script.
    Demonstrates updating the project state with data_source_type=synthetic.
    """
    # This function is intended to be called by other pipeline scripts (e.g., download.py)
    # to update the state after a decision is made.
    # For standalone execution, it performs a self-test.
    import sys
    if len(sys.argv) < 2:
        logger.warning("No project_id provided. Defaulting to PROJ-490-the-effect-of-simulated-social-compariso.")
        project_id = "PROJ-490-the-effect-of-simulated-social-compariso"
    else:
        project_id = sys.argv[1]

    # Simulate a fallback to synthetic data
    update_data_source_type(project_id, 'synthetic')
    logger.info(f"Successfully updated state for {project_id}")


if __name__ == "__main__":
    main()
