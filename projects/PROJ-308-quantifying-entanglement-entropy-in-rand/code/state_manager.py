"""
State Manager Module.

Handles logging and retrieval of unresolved realizations for audit trails.
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Ensure the state directory exists
STATE_DIR = Path("state")
UNRESOLVED_LOG_PATH = STATE_DIR / "unresolved_realizations.json"

def _ensure_state_dir():
    """Ensure the state directory exists."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def _load_unresolved_log() -> List[Dict[str, Any]]:
    """Load the unresolved log from disk."""
    _ensure_state_dir()
    if not UNRESOLVED_LOG_PATH.exists():
        return []
    try:
        with open(UNRESOLVED_LOG_PATH, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def _save_unresolved_log(entries: List[Dict[str, Any]]):
    """Save the unresolved log to disk."""
    _ensure_state_dir()
    with open(UNRESOLVED_LOG_PATH, 'w') as f:
        json.dump(entries, f, indent=2)

def log_unresolved_realization(
    realization_id: int,
    delta: float,
    reason: str,
    details: Optional[Dict[str, Any]] = None
):
    """
    Log a single unresolved realization.

    Args:
        realization_id: Unique ID for the realization.
        delta: Disorder strength parameter.
        reason: Short string describing why it was unresolved.
        details: Optional dict with extra context (e.g., convergence metrics).
    """
    entries = _load_unresolved_log()
    entry = {
        "timestamp": datetime.now().isoformat(),
        "realization_id": realization_id,
        "delta": delta,
        "reason": reason,
        "details": details or {}
    }
    entries.append(entry)
    _save_unresolved_log(entries)

def log_unresolved_batch(
    delta: float,
    realization_ids: List[int],
    reason: str,
    details: Optional[Dict[str, Any]] = None
):
    """
    Log a batch of unresolved realizations.

    Args:
        delta: Disorder strength parameter.
        realization_ids: List of realization IDs.
        reason: Short string describing why they were unresolved.
        details: Optional dict with extra context.
    """
    for rid in realization_ids:
        log_unresolved_realization(rid, delta, reason, details)

def get_unresolved_summary() -> Dict[str, Any]:
    """
    Get a summary of all unresolved realizations.

    Returns:
        Dict with total count and counts by reason.
    """
    entries = _load_unresolved_log()
    by_reason = {}
    for entry in entries:
        reason = entry["reason"]
        by_reason[reason] = by_reason.get(reason, 0) + 1
    return {
        "total_unresolved": len(entries),
        "by_reason": by_reason,
        "last_updated": datetime.now().isoformat()
    }

def get_unresolved_by_delta(delta: float) -> List[Dict[str, Any]]:
    """
    Get unresolved realizations for a specific delta.

    Args:
        delta: Disorder strength parameter.

    Returns:
        List of unresolved entries for that delta.
    """
    entries = _load_unresolved_log()
    return [e for e in entries if abs(e["delta"] - delta) < 1e-6]

def get_unresolved_by_reason(reason: str) -> List[Dict[str, Any]]:
    """
    Get unresolved realizations for a specific reason.

    Args:
        reason: The reason string.

    Returns:
        List of unresolved entries with that reason.
    """
    entries = _load_unresolved_log()
    return [e for e in entries if e["reason"] == reason]

def clear_unresolved_log():
    """Clear the unresolved log (useful for fresh runs)."""
    _ensure_state_dir()
    if UNRESOLVED_LOG_PATH.exists():
        UNRESOLVED_LOG_PATH.unlink()
