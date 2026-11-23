"""
State management module for llmXive.

This module provides utilities for managing project state, including:
- Checksums for data lineage verification
- Execution metadata tracking
- Run state persistence

The state directory is used to store small, critical metadata files
that track the provenance and status of generated artifacts.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import json
import logging

# Configure logger for this module
_logger = logging.getLogger(__name__)

# Default state directory path (relative to project root)
STATE_DIR = Path("state")

def get_state_path(filename: str) -> Path:
    """
    Construct the full path for a state file.

    Args:
        filename: Name of the state file (e.g., 'checksums.yaml', 'run_state.json')

    Returns:
        Absolute Path object pointing to the state file
    """
    return STATE_DIR / filename

def ensure_state_dir() -> None:
    """
    Ensure the state directory exists. Creates it if missing.
    """
    if not STATE_DIR.exists():
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        _logger.info(f"Created state directory: {STATE_DIR}")
    else:
        _logger.debug(f"State directory already exists: {STATE_DIR}")

def load_state_file(filename: str) -> Optional[Dict[str, Any]]:
    """
    Load a JSON state file.

    Args:
        filename: Name of the state file in the state directory

    Returns:
        Dictionary containing the state data, or None if file doesn't exist
    """
    ensure_state_dir()
    filepath = get_state_path(filename)
    if not filepath.exists():
        _logger.warning(f"State file not found: {filepath}")
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        _logger.error(f"Failed to parse state file {filepath}: {e}")
        return None

def save_state_file(filename: str, data: Dict[str, Any]) -> None:
    """
    Save a dictionary to a JSON state file.

    Args:
        filename: Name of the state file in the state directory
        data: Dictionary to serialize and save
    """
    ensure_state_dir()
    filepath = get_state_path(filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, sort_keys=True)
    _logger.info(f"Saved state file: {filepath}")

def update_state_field(filename: str, field_name: str, value: Any) -> None:
    """
    Update a single field in an existing state file.
    If the file doesn't exist, creates it with the new field.

    Args:
        filename: Name of the state file
        field_name: Key to update or create
        value: Value to assign
    """
    current_data = load_state_file(filename) or {}
    current_data[field_name] = value
    save_state_file(filename, current_data)

__all__ = [
    'STATE_DIR',
    'get_state_path',
    'ensure_state_dir',
    'load_state_file',
    'save_state_file',
    'update_state_field'
]