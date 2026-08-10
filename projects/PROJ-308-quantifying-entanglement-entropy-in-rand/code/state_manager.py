"""
State Manager Module for Metadata Logging.

This module handles the logging of 'numerically unresolved' realizations to
ensure an audit trail as per Constitution Principle IV. It manages both
the `data/raw/metadata.json` file and the `state/` directory records.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Constants for paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
STATE_DIR = PROJECT_ROOT / "state"
METADATA_FILE = DATA_RAW_DIR / "metadata.json"
UNRESOLVED_LOG_FILE = STATE_DIR / "unresolved_log.json"

def _ensure_directories():
    """Ensure required directories exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def _load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load JSON from file, returning empty structure if not found."""
    if not file_path.exists():
        return {"unresolved_realizations": [], "summary": {}}
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"unresolved_realizations": [], "summary": {}}

def _save_json_file(file_path: Path, data: Dict[str, Any]):
    """Save data to JSON file with indentation."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def log_unresolved_realization(
    realization_id: int,
    delta: float,
    L: int,
    reason: str,
    timestamp: Optional[datetime] = None
) -> None:
    """
    Log a single numerically unresolved realization.

    Args:
        realization_id: Unique ID for the realization.
        delta: Disorder strength parameter.
        L: Chain length.
        reason: String describing why it was unresolved (e.g., "TEBD did not converge").
        timestamp: Optional timestamp (defaults to now).
    """
    _ensure_directories()
    if timestamp is None:
        timestamp = datetime.now()

    entry = {
        "realization_id": realization_id,
        "delta": delta,
        "L": L,
        "reason": reason,
        "timestamp": timestamp.isoformat()
    }

    # Update metadata.json
    metadata = _load_json_file(METADATA_FILE)
    if "unresolved_realizations" not in metadata:
        metadata["unresolved_realizations"] = []
    metadata["unresolved_realizations"].append(entry)
    _save_json_file(METADATA_FILE, metadata)

    # Update state/unresolved_log.json for audit trail
    state_log = _load_json_file(UNRESOLVED_LOG_FILE)
    if "unresolved_realizations" not in state_log:
        state_log["unresolved_realizations"] = []
    state_log["unresolved_realizations"].append(entry)
    
    # Update summary counts
    reason_counts = state_log.get("summary", {}).get("reason_counts", {})
    reason_counts[reason] = reason_counts.get(reason, 0) + 1
    state_log["summary"] = {
        "total_unresolved": len(state_log["unresolved_realizations"]),
        "reason_counts": reason_counts,
        "last_updated": timestamp.isoformat()
    }
    _save_json_file(UNRESOLVED_LOG_FILE, state_log)

def log_unresolved_batch(
    entries: List[Dict[str, Any]],
    timestamp: Optional[datetime] = None
) -> None:
    """
    Log a batch of unresolved realizations.

    Args:
        entries: List of dicts with keys: realization_id, delta, L, reason.
        timestamp: Optional timestamp.
    """
    for entry in entries:
        log_unresolved_realization(
            realization_id=entry["realization_id"],
            delta=entry["delta"],
            L=entry["L"],
            reason=entry["reason"],
            timestamp=timestamp
        )

def get_unresolved_summary() -> Dict[str, Any]:
    """
    Get the current summary of unresolved realizations.

    Returns:
        Dict containing total count and breakdown by reason.
    """
    _ensure_directories()
    state_log = _load_json_file(UNRESOLVED_LOG_FILE)
    return state_log.get("summary", {"total_unresolved": 0, "reason_counts": {}})

def clear_unresolved_log() -> None:
    """Clear the unresolved log (useful for fresh runs, but keep metadata)."""
    _ensure_directories()
    # Clear state log but keep metadata for historical record
    state_log = {
        "unresolved_realizations": [],
        "summary": {
            "total_unresolved": 0,
            "reason_counts": {},
            "last_updated": datetime.now().isoformat()
        }
    }
    _save_json_file(UNRESOLVED_LOG_FILE, state_log)

def get_unresolved_by_delta(delta: float) -> List[Dict[str, Any]]:
    """Get all unresolved realizations for a specific delta."""
    state_log = _load_json_file(UNRESOLVED_LOG_FILE)
    return [
        e for e in state_log.get("unresolved_realizations", [])
        if abs(e["delta"] - delta) < 1e-6
    ]

def get_unresolved_by_reason(reason: str) -> List[Dict[str, Any]]:
    """Get all unresolved realizations with a specific reason."""
    state_log = _load_json_file(UNRESOLVED_LOG_FILE)
    return [
        e for e in state_log.get("unresolved_realizations", [])
        if e["reason"] == reason
    ]
