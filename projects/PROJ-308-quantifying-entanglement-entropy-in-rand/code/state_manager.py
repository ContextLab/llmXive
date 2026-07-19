"""
State Manager Module for PROJ-308

Handles logging of numerically unresolved realizations to ensure audit trails
as required by Constitution Principle IV.

This module provides functionality to log, summarize, and manage the state
of realizations that failed to converge or were flagged as 'numerically unresolved'
during ground state computation.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Constants for file paths
METADATA_FILE = "data/raw/metadata.json"
STATE_DIR = "state"
UNRESOLVED_LOG_FILE = "state/unresolved_realizations.json"

def _ensure_directories():
    """Ensure required directories exist."""
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    Path("state").mkdir(parents=True, exist_ok=True)

def _load_metadata() -> Dict[str, Any]:
    """Load existing metadata file or create a new one."""
    _ensure_directories()
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {
        "project_id": "PROJ-308-quantifying-entanglement-entropy-in-rand",
        "created_at": datetime.utcnow().isoformat(),
        "unresolved_realizations": [],
        "summary": {
            "total_unresolved": 0,
            "by_reason": {}
        }
    }

def _save_metadata(metadata: Dict[str, Any]) -> None:
    """Save metadata to file."""
    _ensure_directories()
    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

def _load_unresolved_log() -> List[Dict[str, Any]]:
    """Load unresolved realizations log."""
    _ensure_directories()
    if os.path.exists(UNRESOLVED_LOG_FILE):
        with open(UNRESOLVED_LOG_FILE, 'r') as f:
            return json.load(f)
    return []

def _save_unresolved_log(log: List[Dict[str, Any]]) -> None:
    """Save unresolved realizations log."""
    _ensure_directories()
    with open(UNRESOLVED_LOG_FILE, 'w') as f:
        json.dump(log, f, indent=2)

def _update_summary(metadata: Dict[str, Any]) -> None:
    """Update the summary statistics in metadata."""
    unresolved_list = metadata.get("unresolved_realizations", [])
    total = len(unresolved_list)
    
    # Count by reason
    reason_counts = {}
    for entry in unresolved_list:
        reason = entry.get("reason", "unknown")
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
    
    metadata["summary"] = {
        "total_unresolved": total,
        "by_reason": reason_counts
    }

def log_unresolved_realization(
    realization_id: int,
    delta: float,
    L: int,
    reason: str,
    timestamp: Optional[str] = None,
    additional_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a single numerically unresolved realization.
    
    Args:
        realization_id: Unique identifier for the realization
        delta: Disorder strength parameter
        L: Chain length
        reason: Description of why the realization was unresolved
        timestamp: ISO format timestamp (defaults to current time)
        additional_info: Optional dictionary of additional diagnostic info
    """
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()
    
    entry = {
        "realization_id": realization_id,
        "delta": delta,
        "L": L,
        "reason": reason,
        "timestamp": timestamp,
        "additional_info": additional_info or {}
    }
    
    # Update metadata.json
    metadata = _load_metadata()
    metadata["unresolved_realizations"].append(entry)
    _update_summary(metadata)
    _save_metadata(metadata)
    
    # Also maintain a detailed log in state/
    log = _load_unresolved_log()
    log.append(entry)
    _save_unresolved_log(log)

def log_unresolved_batch(
    entries: List[Dict[str, Any]]
) -> None:
    """
    Log multiple unresolved realizations in batch.
    
    Args:
        entries: List of dictionaries containing realization details.
                Each entry should have: realization_id, delta, L, reason
                Optional: timestamp, additional_info
    """
    for entry in entries:
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.utcnow().isoformat()
        if "additional_info" not in entry:
            entry["additional_info"] = {}
    
    # Update metadata.json
    metadata = _load_metadata()
    metadata["unresolved_realizations"].extend(entries)
    _update_summary(metadata)
    _save_metadata(metadata)
    
    # Also maintain a detailed log in state/
    log = _load_unresolved_log()
    log.extend(entries)
    _save_unresolved_log(log)

def get_unresolved_summary() -> Dict[str, Any]:
    """
    Get a summary of all unresolved realizations.
    
    Returns:
        Dictionary containing summary statistics:
        - total_unresolved: Total count
        - by_reason: Breakdown by reason type
        - recent_entries: Last 10 entries for quick inspection
    """
    metadata = _load_metadata()
    summary = metadata.get("summary", {})
    unresolved_list = metadata.get("unresolved_realizations", [])
    
    return {
        "total_unresolved": summary.get("total_unresolved", 0),
        "by_reason": summary.get("by_reason", {}),
        "recent_entries": unresolved_list[-10:] if len(unresolved_list) > 10 else unresolved_list,
        "metadata_file": METADATA_FILE,
        "log_file": UNRESOLVED_LOG_FILE
    }

def clear_unresolved_log() -> None:
    """
    Clear all unresolved realization logs.
    
    WARNING: This should only be used for testing or when starting a fresh
    analysis run. In production, logs should be preserved for audit trails.
    """
    _ensure_directories()
    
    # Clear metadata
    metadata = {
        "project_id": "PROJ-308-quantifying-entanglement-entropy-in-rand",
        "created_at": datetime.utcnow().isoformat(),
        "unresolved_realizations": [],
        "summary": {
            "total_unresolved": 0,
            "by_reason": {}
        }
    }
    _save_metadata(metadata)
    
    # Clear detailed log
    _save_unresolved_log([])

def get_unresolved_by_delta(delta: float, tolerance: float = 1e-6) -> List[Dict[str, Any]]:
    """
    Get all unresolved realizations for a specific delta value.
    
    Args:
        delta: Disorder strength to filter by
        tolerance: Numerical tolerance for float comparison
        
    Returns:
        List of unresolved realization entries matching the delta
    """
    metadata = _load_metadata()
    unresolved_list = metadata.get("unresolved_realizations", [])
    
    return [
        entry for entry in unresolved_list
        if abs(entry.get("delta", 0) - delta) < tolerance
    ]

def get_unresolved_by_reason(reason: str) -> List[Dict[str, Any]]:
    """
    Get all unresolved realizations with a specific reason.
    
    Args:
        reason: Reason string to filter by
        
    Returns:
        List of unresolved realization entries matching the reason
    """
    metadata = _load_metadata()
    unresolved_list = metadata.get("unresolved_realizations", [])
    
    return [
        entry for entry in unresolved_list
        if entry.get("reason", "").lower() == reason.lower()
    ]
