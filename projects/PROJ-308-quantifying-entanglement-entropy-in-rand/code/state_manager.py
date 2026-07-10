"""
State Manager Module

Handles logging of 'numerically unresolved' realizations to ensure audit trail
per Constitution Principle IV. Logs are stored in data/raw/metadata.json
and state/ directory for versioning and tracking.
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Ensure project root structure
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
STATE_DIR = PROJECT_ROOT / "state"
METADATA_FILE = DATA_RAW_DIR / "metadata.json"
UNRESOLVED_LOG_FILE = STATE_DIR / "unresolved_realizations.json"

def _ensure_directories():
    """Ensure required directories exist."""
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def _load_existing_metadata() -> Dict[str, Any]:
    """Load existing metadata file or return empty structure."""
    if METADATA_FILE.exists():
        with open(METADATA_FILE, 'r') as f:
            return json.load(f)
    return {
        "created_at": datetime.utcnow().isoformat(),
        "unresolved_count": 0,
        "unresolved_realizations": []
    }

def _load_existing_unresolved_log() -> List[Dict[str, Any]]:
    """Load existing unresolved log or return empty list."""
    if UNRESOLVED_LOG_FILE.exists():
        with open(UNRESOLVED_LOG_FILE, 'r') as f:
            return json.load(f)
    return []

def log_unresolved_realization(
    realization_id: int,
    delta: float,
    reason: str,
    details: Optional[Dict[str, Any]] = None
):
    """
    Log a single 'numerically unresolved' realization.

    Args:
        realization_id: Unique ID for the realization
        delta: Disorder strength parameter
        reason: Short description of why it's unresolved
        details: Optional additional details (e.g., iteration count, final energy)
    """
    _ensure_directories()

    # Update main metadata file
    metadata = _load_existing_metadata()
    metadata["unresolved_count"] = metadata.get("unresolved_count", 0) + 1
    
    entry = {
        "realization_id": realization_id,
        "delta": delta,
        "reason": reason,
        "logged_at": datetime.utcnow().isoformat()
    }
    if details:
        entry["details"] = details
    
    if "unresolved_realizations" not in metadata:
        metadata["unresolved_realizations"] = []
    metadata["unresolved_realizations"].append(entry)

    with open(METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)

    # Update separate unresolved log file
    unresolved_log = _load_existing_unresolved_log()
    unresolved_log.append(entry)
    
    with open(UNRESOLVED_LOG_FILE, 'w') as f:
        json.dump(unresolved_log, f, indent=2)

def log_unresolved_batch(
    unresolved_list: List[Dict[str, Any]],
    delta: float
):
    """
    Log a batch of unresolved realizations.

    Args:
        unresolved_list: List of dicts with 'realization_id', 'reason', and optional 'details'
        delta: Disorder strength parameter for this batch
    """
    for item in unresolved_list:
        log_unresolved_realization(
            realization_id=item["realization_id"],
            delta=delta,
            reason=item["reason"],
            details=item.get("details")
        )

def get_unresolved_summary() -> Dict[str, Any]:
    """
    Get summary of all unresolved realizations.

    Returns:
        Dict with count and list of all unresolved entries
    """
    _ensure_directories()
    return _load_existing_metadata()

def clear_unresolved_log():
    """Clear the unresolved log file (for testing purposes)."""
    if UNRESOLVED_LOG_FILE.exists():
        UNRESOLVED_LOG_FILE.unlink()
    if METADATA_FILE.exists():
        METADATA_FILE.unlink()
