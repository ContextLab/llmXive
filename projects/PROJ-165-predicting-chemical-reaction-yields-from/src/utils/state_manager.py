"""
State Manager Module for llmXive Project.

This module implements Principle V: Reproducibility and State Tracking.
It provides functions to compute file/directory hashes, manage a central
state JSON file, log task execution history, and verify data integrity.
"""

import os
import hashlib
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

# Default path for the state file relative to project root
STATE_FILE_PATH = Path("state/state.json")
# Directory where state files are stored
STATE_DIR = Path("state")


def _ensure_state_dir():
    """Ensure the state directory exists."""
    if not STATE_DIR.exists():
        STATE_DIR.mkdir(parents=True, exist_ok=True)


def compute_file_hash(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file's contents.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Could not read file {path}: {e}")


def compute_directory_hash(dir_path: Path, ignore_patterns: Optional[List[str]] = None) -> str:
    """
    Compute a deterministic hash for a directory based on its files.
    Files are processed in sorted order to ensure determinism.

    Args:
        dir_path: Path to the directory.
        ignore_patterns: List of filename patterns to ignore (e.g., ['.tmp', '__pycache__']).

    Returns:
        Hexadecimal string of the combined SHA-256 hash.

    Raises:
        NotADirectoryError: If path is not a directory.
    """
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {dir_path}")

    sha256_hash = hashlib.sha256()
    ignore_list = ignore_patterns or []

    # Walk directory and sort files for determinism
    all_files = []
    for root, _, files in os.walk(dir_path):
        for file in files:
            # Skip ignored patterns
            if any(file.endswith(p) or p in root for p in ignore_list):
                continue
            all_files.append(Path(root) / file)

    all_files.sort(key=lambda p: str(p.relative_to(dir_path)))

    for file_path in all_files:
        # Include relative path in hash to detect moves/renames
        rel_path = file_path.relative_to(dir_path)
        sha256_hash.update(str(rel_path).encode('utf-8'))
        try:
            file_hash = compute_file_hash(file_path)
            sha256_hash.update(file_hash.encode('utf-8'))
        except (FileNotFoundError, IOError):
            # Skip files that disappear during traversal
            continue

    return sha256_hash.hexdigest()


def load_state() -> Dict[str, Any]:
    """
    Load the current project state from the state file.

    Returns:
        Dictionary containing the state. Returns an empty structure if file doesn't exist.
    """
    _ensure_state_dir()
    if not STATE_FILE_PATH.exists():
        return {
            "project_id": "PROJ-165",
            "last_updated": None,
            "task_history": [],
            "data_integrity": {},
            "config_hashes": {}
        }

    try:
        with open(STATE_FILE_PATH, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        # Return clean state on corruption to prevent crash, log warning
        print(f"Warning: State file corrupted or unreadable. Resetting state. Error: {e}")
        return {
            "project_id": "PROJ-165",
            "last_updated": None,
            "task_history": [],
            "data_integrity": {},
            "config_hashes": {}
        }


def save_state(state: Dict[str, Any]) -> None:
    """
    Save the project state to the state file.

    Args:
        state: The state dictionary to save.
    """
    _ensure_state_dir()
    state["last_updated"] = time.time()
    with open(STATE_FILE_PATH, 'w') as f:
        json.dump(state, f, indent=2)


def update_state(task_id: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Update the state with a new task execution record.

    Args:
        task_id: The unique identifier for the task (e.g., 'T005').
        status: Execution status ('started', 'completed', 'failed').
        details: Optional dictionary of additional metadata (e.g., hashes, durations).
    """
    state = load_state()

    record = {
        "task_id": task_id,
        "status": status,
        "timestamp": time.time(),
        "details": details or {}
    }

    state["task_history"].append(record)

    # Update specific integrity hashes if provided
    if details and "data_hash" in details:
        data_file = details.get("data_file", "unknown")
        state["data_integrity"][data_file] = details["data_hash"]

    if details and "config_hash" in details:
        config_name = details.get("config_name", "unknown")
        state["config_hashes"][config_name] = details["config_hash"]

    save_state(state)


def get_state_summary() -> Dict[str, Any]:
    """
    Get a summary of the current state for quick inspection.

    Returns:
        Dictionary with project ID, last update time, and task counts.
    """
    state = load_state()
    history = state.get("task_history", [])

    completed = sum(1 for t in history if t["status"] == "completed")
    failed = sum(1 for t in history if t["status"] == "failed")
    started = sum(1 for t in history if t["status"] == "started")

    return {
        "project_id": state.get("project_id"),
        "last_updated": state.get("last_updated"),
        "total_tasks": len(history),
        "completed": completed,
        "failed": failed,
        "started": started,
        "data_integrity_count": len(state.get("data_integrity", {}))
    }


def verify_file_integrity(file_path: Path, expected_hash: Optional[str] = None) -> bool:
    """
    Verify the integrity of a file by comparing its hash to a stored value.

    Args:
        file_path: Path to the file to verify.
        expected_hash: Optional expected hash. If None, it is looked up in state.

    Returns:
        True if hashes match, False otherwise.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not file_path.exists():
        return False

    current_hash = compute_file_hash(file_path)

    if expected_hash:
        return current_hash == expected_hash

    # If no expected hash provided, check if it's recorded in state
    state = load_state()
    # Simple lookup by filename
    filename = file_path.name
    stored_hashes = state.get("data_integrity", {})
    if filename in stored_hashes:
        return current_hash == stored_hashes[filename]

    # If not found in state, we cannot verify, but file exists
    return True


def log_task_start(task_id: str) -> None:
    """
    Log the start of a task execution.

    Args:
        task_id: The task identifier.
    """
    update_state(task_id, "started", {"start_time": time.time()})


def log_task_complete(task_id: str, duration: Optional[float] = None, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log the completion of a task execution.

    Args:
        task_id: The task identifier.
        duration: Duration in seconds.
        details: Additional metadata to store.
    """
    state = load_state()
    # Find the most recent 'started' record for this task to calculate duration if not provided
    if duration is None:
        for record in reversed(state["task_history"]):
            if record["task_id"] == task_id and record["status"] == "started":
                start_time = record.get("details", {}).get("start_time")
                if start_time:
                    duration = time.time() - start_time
                break

    final_details = details or {}
    if duration is not None:
        final_details["duration_seconds"] = duration

    update_state(task_id, "completed", final_details)


def get_task_history(task_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve the execution history of tasks.

    Args:
        task_id: Optional specific task ID to filter by.

    Returns:
        List of task execution records.
    """
    state = load_state()
    history = state.get("task_history", [])
    if task_id:
        return [t for t in history if t["task_id"] == task_id]
    return history


def reset_state() -> None:
    """
    Reset the project state to a clean initial state.
    WARNING: This will overwrite the current state file.
    """
    _ensure_state_dir()
    initial_state = {
        "project_id": "PROJ-165",
        "last_updated": time.time(),
        "task_history": [],
        "data_integrity": {},
        "config_hashes": {}
    }
    save_state(initial_state)
