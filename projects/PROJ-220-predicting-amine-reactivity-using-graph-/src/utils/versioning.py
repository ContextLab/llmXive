"""
Versioning and State Management Module.

Implements Constitution Principle V:
- Deterministic state tracking via content-addressable hashing.
- Atomic writes to state files to prevent corruption.
- Project-specific state isolation.
"""

import hashlib
import json
import os
import tempfile
import shutil
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

# Project root is assumed to be the parent of 'src'
# In a real execution context, this might be passed explicitly or found via a marker file.
# For this implementation, we assume the standard layout: <root>/src/utils/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_STATE_DIR = _PROJECT_ROOT / "state" / "projects"
_PROJECT_ID = "PROJ-220-predicting-amine-reactivity-using-graph-"


def _ensure_state_dir() -> Path:
    """Ensure the state directory exists."""
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    return _STATE_DIR


def _compute_hash(data: Union[str, bytes, Dict[str, Any]]) -> str:
    """
    Compute a SHA-256 hash of the input data.
    
    Args:
        data: The data to hash. Can be a string, bytes, or a dictionary.
             If a dictionary, it is serialized to JSON with sorted keys.
             
    Returns:
        A hexadecimal string representing the SHA-256 hash.
    """
    if isinstance(data, dict):
        # Serialize dict to canonical JSON string
        content = json.dumps(data, sort_keys=True, separators=(',', ':'))
        content_bytes = content.encode('utf-8')
    elif isinstance(data, str):
        content_bytes = data.encode('utf-8')
    elif isinstance(data, bytes):
        content_bytes = data
    else:
        raise TypeError(f"Unsupported data type for hashing: {type(data)}")

    return hashlib.sha256(content_bytes).hexdigest()


def _read_state_file(state_path: Path) -> Optional[Dict[str, Any]]:
    """
    Read the current state file if it exists.
    
    Args:
        state_path: Path to the state YAML file.
        
    Returns:
        The parsed dictionary contents, or None if the file does not exist.
    """
    if not state_path.exists():
        return None
    
    with open(state_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def _write_state_atomic(state_path: Path, state: Dict[str, Any]) -> None:
    """
    Write the state to a file atomically using a temporary file and rename.
    
    This ensures that if the write is interrupted, the original file remains intact.
    
    Args:
        state_path: The final destination path for the state file.
        state: The dictionary to serialize and write.
    """
    _ensure_state_dir()
    
    # Create a temporary file in the same directory to ensure atomic rename on the same filesystem
    fd, temp_path = tempfile.mkstemp(
        suffix='.tmp',
        prefix=f"{state_path.stem}_",
        dir=str(state_path.parent)
    )
    
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            # Use sort_keys for deterministic output
            yaml.dump(state, f, default_flow_style=False, sort_keys=True, allow_unicode=True)
        
        # Atomic rename
        shutil.move(temp_path, state_path)
    except Exception:
        # Clean up temp file if something goes wrong
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def update_state(
    key: str,
    value: Any,
    project_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Update the state for a specific project with a new key-value pair.
    
    This function implements Constitution Principle V by:
    1. Reading the existing state (if any).
    2. Updating the state dictionary with the new key-value pair.
    3. Calculating a hash of the new state content.
    4. Writing the state atomically to disk.
    
    Args:
        key: The key to update in the state dictionary.
        value: The new value for the key.
        project_id: Optional project ID override. Defaults to the global PROJECT_ID.
        metadata: Optional additional metadata to include in the state (e.g., timestamp, version).
                
    Returns:
        The updated state dictionary.
        
    Raises:
        IOError: If the state file cannot be read or written.
    """
    pid = project_id or _PROJECT_ID
    state_path = _STATE_DIR / f"{pid}.yaml"
    
    # Read existing state
    current_state = _read_state_file(state_path) or {}
    
    # Update the state
    current_state[key] = value
    
    # Merge metadata if provided
    if metadata:
        if "metadata" not in current_state:
            current_state["metadata"] = {}
        current_state["metadata"].update(metadata)
    
    # Calculate hash of the new state
    state_hash = _compute_hash(current_state)
    current_state["_hash"] = state_hash
    
    # Write atomically
    _write_state_atomic(state_path, current_state)
    
    return current_state


def get_state(project_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve the current state for a specific project.
    
    Args:
        project_id: Optional project ID override. Defaults to the global PROJECT_ID.
        
    Returns:
        The current state dictionary, or an empty dictionary if no state exists.
    """
    pid = project_id or _PROJECT_ID
    state_path = _STATE_DIR / f"{pid}.yaml"
    return _read_state_file(state_path) or {}


def verify_state_integrity(project_id: Optional[str] = None) -> bool:
    """
    Verify that the stored state hash matches the calculated hash of the content.
    
    Args:
        project_id: Optional project ID override. Defaults to the global PROJECT_ID.
        
    Returns:
        True if the state is valid and the hash matches, False otherwise.
    """
    pid = project_id or _PROJECT_ID
    state_path = _STATE_DIR / f"{pid}.yaml"
    
    state = _read_state_file(state_path)
    if not state:
        return False
        
    stored_hash = state.get("_hash")
    if not stored_hash:
        return False
        
    # Recalculate hash excluding the _hash field itself
    content_for_hash = {k: v for k, v in state.items() if k != "_hash"}
    calculated_hash = _compute_hash(content_for_hash)
    
    return stored_hash == calculated_hash
