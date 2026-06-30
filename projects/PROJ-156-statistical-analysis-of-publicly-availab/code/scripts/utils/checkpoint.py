"""
Checkpoint utility for resuming long-running scripts on CI timeout.

Provides functions to save and load intermediate state as JSON files.
State includes progress markers (e.g., last processed game ID) and
partial results to allow resumption without reprocessing completed items.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Ensure the utils directory exists relative to the project root
# Assuming the script is run from the project root or code/scripts
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHECKPOINT_DIR = BASE_DIR / "data" / "checkpoints"

def ensure_checkpoint_dir() -> Path:
    """Ensure the checkpoint directory exists."""
    if not CHECKPOINT_DIR.exists():
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    return CHECKPOINT_DIR

def save_checkpoint(filename: str, state: Dict[str, Any]) -> None:
    """
    Save the current state to a JSON checkpoint file.
    
    Args:
        filename: Name of the checkpoint file (e.g., 'fetch_data_state.json').
        state: Dictionary containing the state to save (e.g., processed games, counters).
    """
    ensure_checkpoint_dir()
    filepath = CHECKPOINT_DIR / filename
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, default=str)
        print(f"Checkpoint saved: {filepath}")
    except Exception as e:
        raise RuntimeError(f"Failed to save checkpoint to {filepath}: {e}")

def load_checkpoint(filename: str) -> Optional[Dict[str, Any]]:
    """
    Load the state from a JSON checkpoint file if it exists.
    
    Args:
        filename: Name of the checkpoint file.
    
    Returns:
        The state dictionary if the file exists, otherwise None.
    """
    filepath = CHECKPOINT_DIR / filename
    
    if not filepath.exists():
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Warning: Checkpoint file {filepath} is corrupted. Ignoring.")
        return None
    except Exception as e:
        raise RuntimeError(f"Failed to load checkpoint from {filepath}: {e}")

def delete_checkpoint(filename: str) -> bool:
    """
    Delete a checkpoint file after successful completion.
    
    Args:
        filename: Name of the checkpoint file.
    
    Returns:
        True if deleted, False if file didn't exist.
    """
    filepath = CHECKPOINT_DIR / filename
    if filepath.exists():
        try:
            filepath.unlink()
            print(f"Checkpoint deleted: {filepath}")
            return True
        except Exception as e:
            print(f"Warning: Failed to delete checkpoint {filepath}: {e}")
            return False
    return False

def get_checkpoint_path(filename: str) -> Path:
    """Return the full path to a checkpoint file."""
    return CHECKPOINT_DIR / filename
