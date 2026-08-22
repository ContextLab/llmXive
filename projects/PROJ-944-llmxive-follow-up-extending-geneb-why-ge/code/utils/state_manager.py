"""
State management utilities for llmXive projects.
Handles initialization and updating of the project state YAML file.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

import yaml


def ensure_state_dir(project_id: str) -> Path:
    """
    Ensure the state directory for a specific project exists.

    Args:
        project_id: The project identifier (e.g., PROJ-944-...)

    Returns:
        Path to the project state directory.
    """
    base_dir = Path("state")
    project_dir = base_dir / "projects" / project_id
    project_dir.mkdir(parents=True, exist_ok=True)
    return project_dir


def load_state_file(project_id: str) -> Dict[str, Any]:
    """
    Load the state YAML file for a project. If it doesn't exist,
    returns an empty structure with the required top-level keys.

    Args:
        project_id: The project identifier.

    Returns:
        Dictionary representing the state file contents.
    """
    state_dir = ensure_state_dir(project_id)
    state_file = state_dir / f"{project_id}.yaml"

    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
                if data is None:
                    data = {}
                return data
            except yaml.YAMLError:
                # If file is corrupted, start fresh with default structure
                return {}
    else:
        return {}


def initialize_state_file(project_id: str, force: bool = False) -> Path:
    """
    Initialize the project state YAML file with the required structure
    if it is missing or if force=True.

    The required structure includes:
    - artifact_hashes: map for storing file checksums

    Args:
        project_id: The project identifier.
        force: If True, overwrite existing file even if it exists.

    Returns:
        Path to the created/updated state file.
    """
    state_dir = ensure_state_dir(project_id)
    state_file = state_dir / f"{project_id}.yaml"

    if state_file.exists() and not force:
        # Check if artifact_hashes key exists
        current_data = load_state_file(project_id)
        if "artifact_hashes" in current_data:
            return state_file

    # Create or overwrite with default structure
    default_structure = {
        "project_id": project_id,
        "artifact_hashes": {}
    }

    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(
            default_structure,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True
        )

    return state_file


def update_state_file(project_id: str, updates: Dict[str, Any]) -> Path:
    """
    Update the state YAML file with new values, merging with existing data.

    Args:
        project_id: The project identifier.
        updates: Dictionary of values to update/merge into the state.

    Returns:
        Path to the updated state file.
    """
    state_dir = ensure_state_dir(project_id)
    state_file = state_dir / f"{project_id}.yaml"

    # Load existing data
    current_data = load_state_file(project_id)

    # Merge updates
    for key, value in updates.items():
        if isinstance(value, dict) and key in current_data and isinstance(current_data[key], dict):
            current_data[key].update(value)
        else:
            current_data[key] = value

    # Ensure artifact_hashes exists if not explicitly set
    if "artifact_hashes" not in current_data:
        current_data["artifact_hashes"] = {}

    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(
            current_data,
            f,
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True
        )

    return state_file
