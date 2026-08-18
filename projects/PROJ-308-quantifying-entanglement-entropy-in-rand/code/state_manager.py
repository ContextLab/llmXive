"""
State Manager Module for PROJ-308.

Handles logging of numerically unresolved realizations to ensure audit trails
as per Constitution Principle IV.
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Project root relative to code/
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
STATE_DIR = PROJECT_ROOT / "state"
METADATA_FILE = DATA_RAW_DIR / "metadata.json"
UNRESOLVED_LOG_FILE = STATE_DIR / "unresolved_realizations.json"

def _ensure_dirs():
    """Ensure required directories exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def _load_metadata() -> Dict[str, Any]:
    """Load existing metadata or return a fresh structure."""
    _ensure_dirs()
    if METADATA_FILE.exists():
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {
        "project_id": "PROJ-308-quantifying-entanglement-entropy-in-rand",
        "generated_at": datetime.utcnow().isoformat(),
        "unresolved_summary": {
            "total_count": 0,
            "by_delta": {},
            "by_reason": {}
        },
        "unresolved_details": []
    }

def _save_metadata(data: Dict[str, Any]):
    """Save metadata to disk."""
    _ensure_dirs()
    with open(METADATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def _load_unresolved_log() -> List[Dict[str, Any]]:
    """Load the detailed unresolved log."""
    _ensure_dirs()
    if UNRESOLVED_LOG_FILE.exists():
        with open(UNRESOLVED_LOG_FILE, 'r') as f:
            return json.load(f)
    return []

def _save_unresolved_log(log: List[Dict[str, Any]]):
    """Save the detailed unresolved log."""
    _ensure_dirs()
    with open(UNRESOLVED_LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2)

def log_unresolved_realization(delta: float, realization_id: int, reason: str, details: Optional[Dict[str, Any]] = None):
    """
    Log a single numerically unresolved realization.

    Args:
        delta: Disorder strength parameter.
        realization_id: Unique ID for the realization.
        reason: Short string explaining why it was unresolved (e.g., "TEBD convergence failure").
        details: Optional dict with extra context (e.g., iterations, final energy).
    """
    _ensure_dirs()
    timestamp = datetime.utcnow().isoformat()
    entry = {
        "timestamp": timestamp,
        "delta": delta,
        "realization_id": realization_id,
        "reason": reason,
        "details": details or {}
    }

    # Update detailed log
    log = _load_unresolved_log()
    log.append(entry)
    _save_unresolved_log(log)

    # Update summary in metadata
    metadata = _load_metadata()
    meta = metadata["unresolved_summary"]
    meta["total_count"] += 1

    # Update by_delta
    delta_key = f"{delta:.4f}"
    if delta_key not in meta["by_delta"]:
        meta["by_delta"][delta_key] = 0
    meta["by_delta"][delta_key] += 1

    # Update by_reason
    if reason not in meta["by_reason"]:
        meta["by_reason"][reason] = 0
    meta["by_reason"][reason] += 1

    # Update timestamp
    metadata["generated_at"] = timestamp
    _save_metadata(metadata)

def log_unresolved_batch(delta: float, realization_ids: List[int], reason: str, details: Optional[Dict[str, Any]] = None):
    """
    Log a batch of numerically unresolved realizations.

    Args:
        delta: Disorder strength parameter.
        realization_ids: List of realization IDs.
        reason: Short string explaining the failure reason.
        details: Optional dict with extra context.
    """
    for rid in realization_ids:
        log_unresolved_realization(delta, rid, reason, details)

def get_unresolved_summary() -> Dict[str, Any]:
    """
    Retrieve the current unresolved summary from metadata.

    Returns:
        Dict with total_count, by_delta, and by_reason.
    """
    metadata = _load_metadata()
    return metadata["unresolved_summary"]

def get_unresolved_by_delta(delta: float) -> List[Dict[str, Any]]:
    """
    Get all unresolved entries for a specific delta.

    Args:
        delta: Disorder strength to filter by.

    Returns:
        List of unresolved entries for that delta.
    """
    log = _load_unresolved_log()
    return [e for e in log if abs(e["delta"] - delta) < 1e-6]

def get_unresolved_by_reason(reason: str) -> List[Dict[str, Any]]:
    """
    Get all unresolved entries for a specific reason.

    Args:
        reason: Reason string to filter by.

    Returns:
        List of unresolved entries with that reason.
    """
    log = _load_unresolved_log()
    return [e for e in log if e["reason"] == reason]

def clear_unresolved_log():
    """
    Clear the unresolved log and reset the summary in metadata.
    Useful for starting a fresh run or resetting state.
    """
    _ensure_dirs()
    # Clear detailed log
    _save_unresolved_log([])

    # Reset summary in metadata
    metadata = {
        "project_id": "PROJ-308-quantifying-entanglement-entropy-in-rand",
        "generated_at": datetime.utcnow().isoformat(),
        "unresolved_summary": {
            "total_count": 0,
            "by_delta": {},
            "by_reason": {}
        },
        "unresolved_details": []
    }
    _save_metadata(metadata)
