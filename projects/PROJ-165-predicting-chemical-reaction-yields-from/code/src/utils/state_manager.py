import os
import hashlib
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

# Global state file path relative to project root
STATE_FILE_PATH = Path("state/project_state.json")
TASK_HISTORY_KEY = "task_history"
LAST_UPDATED_KEY = "last_updated"
STATE_HASH_KEY = "state_hash"

def _ensure_state_dir() -> Path:
    """Ensure the state directory exists."""
    state_dir = STATE_FILE_PATH.parent
    if not state_dir.exists():
        state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir

def _load_current_state() -> Dict[str, Any]:
    """Load the current state file or return an empty structure if it doesn't exist."""
    if not STATE_FILE_PATH.exists():
        return {
            LAST_UPDATED_KEY: None,
            STATE_HASH_KEY: None,
            TASK_HISTORY_KEY: []
        }
    try:
        with open(STATE_FILE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # If corrupted or unreadable, start fresh but log a warning in a real system
        return {
            LAST_UPDATED_KEY: None,
            STATE_HASH_KEY: None,
            TASK_HISTORY_KEY: []
        }

def _save_state(state: Dict[str, Any]) -> None:
    """Save the state dictionary to the state file."""
    _ensure_state_dir()
    with open(STATE_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, default=str)

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def compute_directory_hash(dir_path: Path) -> str:
    """Compute a combined hash of all files in a directory recursively."""
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")
    
    sha256_hash = hashlib.sha256()
    # Sort files to ensure deterministic order
    for file_path in sorted(dir_path.rglob("*")):
        if file_path.is_file():
            # Include relative path in hash to detect file moves
            rel_path = file_path.relative_to(dir_path)
            sha256_hash.update(str(rel_path).encode('utf-8'))
            # Update content hash
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def load_state() -> Dict[str, Any]:
    """Load the entire project state."""
    return _load_current_state()

def save_state(state: Dict[str, Any]) -> None:
    """Save the project state."""
    _save_state(state)

def update_state(updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the project state with new values and refresh timestamp.
    Returns the updated state.
    """
    state = _load_current_state()
    state.update(updates)
    state[LAST_UPDATED_KEY] = time.time()
    _save_state(state)
    return state

def get_state_summary() -> Dict[str, Any]:
    """Get a summary of the current state (excluding large history if needed)."""
    state = _load_current_state()
    return {
        "last_updated": state.get(LAST_UPDATED_KEY),
        "state_hash": state.get(STATE_HASH_KEY),
        "total_tasks_logged": len(state.get(TASK_HISTORY_KEY, []))
    }

def verify_file_integrity(file_path: Path, expected_hash: Optional[str] = None) -> bool:
    """
    Verify a file's integrity.
    If expected_hash is provided, compare against it.
    Otherwise, just ensure the file is readable and compute its hash.
    """
    if not file_path.exists():
        return False
    
    current_hash = compute_file_hash(file_path)
    
    if expected_hash is not None:
        return current_hash == expected_hash
    
    return True

def log_task_start(task_id: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Log the start of a task in the state history."""
    state = _load_current_state()
    history = state.get(TASK_HISTORY_KEY, [])
    
    entry = {
        "task_id": task_id,
        "status": "started",
        "timestamp": time.time(),
        "details": details or {}
    }
    history.append(entry)
    state[TASK_HISTORY_KEY] = history
    state[LAST_UPDATED_KEY] = time.time()
    _save_state(state)

def log_task_complete(task_id: str, outcome: str = "success", details: Optional[Dict[str, Any]] = None) -> None:
    """Log the completion of a task in the state history."""
    state = _load_current_state()
    history = state.get(TASK_HISTORY_KEY, [])
    
    # Find the last entry for this task_id and update it, or add a new one if not found
    # For simplicity in this implementation, we append a new completion entry
    entry = {
        "task_id": task_id,
        "status": "completed",
        "outcome": outcome,
        "timestamp": time.time(),
        "details": details or {}
    }
    history.append(entry)
    state[TASK_HISTORY_KEY] = history
    state[LAST_UPDATED_KEY] = time.time()
    _save_state(state)

def get_task_history(task_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get the task history.
    If task_id is provided, filter for that specific task.
    """
    state = _load_current_state()
    history = state.get(TASK_HISTORY_KEY, [])
    
    if task_id:
        return [entry for entry in history if entry.get("task_id") == task_id]
    
    return history

def reset_state() -> None:
    """Reset the project state to empty."""
    state = {
        LAST_UPDATED_KEY: None,
        STATE_HASH_KEY: None,
        TASK_HISTORY_KEY: []
    }
    _save_state(state)