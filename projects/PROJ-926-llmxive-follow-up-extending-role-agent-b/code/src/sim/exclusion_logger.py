import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

# Default path relative to project root
DEFAULT_EXCLUSION_PATH = "data/raw/excluded_log.json"

_exclusion_log: List[Dict[str, Any]] = []
_exclusion_path: str = DEFAULT_EXCLUSION_PATH

def set_exclusion_path(path: str) -> None:
    """Set the file path for the exclusion log."""
    global _exclusion_path
    _exclusion_path = path
    # Ensure directory exists
    os.makedirs(os.path.dirname(_exclusion_path) or ".", exist_ok=True)

def log_excluded_trajectory(
    trajectory_id: str,
    reason: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a single excluded trajectory to the in-memory buffer.
    
    Args:
        trajectory_id: Unique ID of the excluded trajectory.
        reason: Short description of why it was excluded (e.g., "ambiguous root cause").
        details: Optional additional context (action log snippet, validation error, etc.).
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "trajectory_id": trajectory_id,
        "reason": reason,
        "details": details or {}
    }
    _exclusion_log.append(entry)

def log_excluded_trajectories(entries: List[Dict[str, Any]]) -> None:
    """Log multiple excluded trajectories at once."""
    for entry in entries:
        if "trajectory_id" not in entry or "reason" not in entry:
            raise ValueError("Each entry must contain 'trajectory_id' and 'reason'.")
        entry.setdefault("timestamp", datetime.utcnow().isoformat())
        _exclusion_log.append(entry)

def get_exclusion_log() -> List[Dict[str, Any]]:
    """Return the current in-memory exclusion log."""
    return _exclusion_log.copy()

def clear_exclusion_log() -> None:
    """Clear the in-memory exclusion log."""
    global _exclusion_log
    _exclusion_log = []

def run() -> None:
    """
    Persist the in-memory exclusion log to disk.
    This should be called after generation loops to write `data/raw/excluded_log.json`.
    """
    os.makedirs(os.path.dirname(_exclusion_path) or ".", exist_ok=True)
    with open(_exclusion_path, "w", encoding="utf-8") as f:
        json.dump(_exclusion_log, f, indent=2)
