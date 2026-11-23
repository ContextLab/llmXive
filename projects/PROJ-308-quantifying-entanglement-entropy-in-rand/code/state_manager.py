"""
State Manager Module for PROJ-308.

Handles logging of numerically unresolved realizations to ensure an audit trail
as per Constitution Principle IV.
"""
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Define paths relative to project root
_DATA_RAW_DIR = Path("data/raw")
_STATE_DIR = Path("state")
_METADATA_FILE = _DATA_RAW_DIR / "metadata.json"
_UNRESOLVED_LOG_FILE = _STATE_DIR / "unresolved_log.json"

def _ensure_dirs():
    """Ensure required directories exist."""
    _DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    _STATE_DIR.mkdir(parents=True, exist_ok=True)

def _load_json_file(filepath: Path) -> Dict[str, Any]:
    """Load JSON from file, returning empty structure if not found."""
    if not filepath.exists():
        return {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        # If file is corrupted or unreadable, start fresh to prevent data loss
        # In a real pipeline, this might trigger an alert
        print(f"Warning: Could not load {filepath}, starting fresh. Error: {e}")
        return {}

def _save_json_file(filepath: Path, data: Dict[str, Any]):
    """Save data to JSON file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)

def log_unresolved_realization(
    realization_id: int,
    delta: float,
    L: int,
    reason: str,
    timestamp: Optional[str] = None
):
    """
    Log a single numerically unresolved realization.

    Args:
        realization_id: Unique ID for the realization.
        delta: Disorder strength parameter.
        L: System size.
        reason: Description of why the realization was unresolved.
        timestamp: ISO format timestamp (defaults to now).
    """
    _ensure_dirs()
    now = timestamp or datetime.utcnow().isoformat()

    # Load existing metadata
    metadata = _load_json_file(_METADATA_FILE)
    if "unresolved_realizations" not in metadata:
        metadata["unresolved_realizations"] = []

    entry = {
        "realization_id": realization_id,
        "delta": delta,
        "L": L,
        "reason": reason,
        "timestamp": now
    }
    metadata["unresolved_realizations"].append(entry)

    # Save updated metadata
    _save_json_file(_METADATA_FILE, metadata)

    # Also log to the specific unresolved log in state/
    state_log = _load_json_file(_UNRESOLVED_LOG_FILE)
    if "entries" not in state_log:
        state_log["entries"] = []
    state_log["entries"].append(entry)
    state_log["last_updated"] = now
    _save_json_file(_UNRESOLVED_LOG_FILE, state_log)

def log_unresolved_batch(
    batch_id: str,
    deltas: List[float],
    L: int,
    reasons: List[str],
    count: int
):
    """
    Log a batch of unresolved realizations.

    Args:
        batch_id: Identifier for the batch.
        deltas: List of delta values processed.
        L: System size.
        reasons: List of reasons corresponding to the failures.
        count: Total number of unresolved realizations in this batch.
    """
    _ensure_dirs()
    now = datetime.utcnow().isoformat()

    batch_entry = {
        "batch_id": batch_id,
        "deltas": deltas,
        "L": L,
        "reasons": reasons,
        "count": count,
        "timestamp": now
    }

    # Update metadata
    metadata = _load_json_file(_METADATA_FILE)
    if "unresolved_batches" not in metadata:
        metadata["unresolved_batches"] = []
    metadata["unresolved_batches"].append(batch_entry)
    _save_json_file(_METADATA_FILE, metadata)

    # Update state log
    state_log = _load_json_file(_UNRESOLVED_LOG_FILE)
    if "batches" not in state_log:
        state_log["batches"] = []
    state_log["batches"].append(batch_entry)
    state_log["last_updated"] = now
    _save_json_file(_UNRESOLVED_LOG_FILE, state_log)

def get_unresolved_summary() -> Dict[str, Any]:
    """
    Get a summary of all unresolved realizations.

    Returns:
        Dictionary with total count, count by reason, and count by delta.
    """
    metadata = _load_json_file(_METADATA_FILE)
    unresolved = metadata.get("unresolved_realizations", [])

    total = len(unresolved)
    by_reason: Dict[str, int] = {}
    by_delta: Dict[float, int] = {}

    for entry in unresolved:
        reason = entry.get("reason", "Unknown")
        delta = entry.get("delta", 0.0)

        by_reason[reason] = by_reason.get(reason, 0) + 1
        by_delta[delta] = by_delta.get(delta, 0) + 1

    return {
        "total_unresolved": total,
        "count_by_reason": by_reason,
        "count_by_delta": by_delta,
        "last_updated": metadata.get("last_updated", None)
    }

def get_unresolved_by_delta(delta: float) -> List[Dict[str, Any]]:
    """
    Retrieve all unresolved realizations for a specific delta.

    Args:
        delta: The disorder strength to filter by.

    Returns:
        List of unresolved realization entries.
    """
    metadata = _load_json_file(_METADATA_FILE)
    unresolved = metadata.get("unresolved_realizations", [])
    return [e for e in unresolved if abs(e.get("delta", 0.0) - delta) < 1e-6]

def get_unresolved_by_reason(reason: str) -> List[Dict[str, Any]]:
    """
    Retrieve all unresolved realizations for a specific reason.

    Args:
        reason: The reason string to filter by.

    Returns:
        List of unresolved realization entries.
    """
    metadata = _load_json_file(_METADATA_FILE)
    unresolved = metadata.get("unresolved_realizations", [])
    return [e for e in unresolved if e.get("reason", "") == reason]

def clear_unresolved_log():
    """
    Clear the unresolved log files. Use with caution.
    """
    _ensure_dirs()
    # Initialize with empty structure to ensure files exist but are empty
    _save_json_file(_METADATA_FILE, {"unresolved_realizations": [], "unresolved_batches": []})
    _save_json_file(_UNRESOLVED_LOG_FILE, {"entries": [], "batches": [], "last_updated": datetime.utcnow().isoformat()})
