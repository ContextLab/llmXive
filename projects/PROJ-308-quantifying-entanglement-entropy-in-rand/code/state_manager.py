import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

def log_unresolved_realization(realization_id: int, reason: str) -> None:
    """Logs details of a numerically unresolved realization."""
    state_dir = Path("state")
    state_dir.mkdir(exist_ok=True)
    unresolved_file = state_dir / "unresolved_realizations.json"
    data = []
    if unresolved_file.exists():
        with open(unresolved_file, "r") as f:
            data = json.load(f)
    data.append({"realization_id": realization_id, "reason": reason, "timestamp": datetime.now().isoformat()})
    with open(unresolved_file, "w") as f:
        json.dump(data, f, indent=4)

def log_unresolved_batch(realizations: List[int], reason: str) -> None:
    """Logs the details of a batch of unresolved realizations."""
    for realization_id in realizations:
        log_unresolved_realization(realization_id, reason)

def get_unresolved_summary() -> Dict[str, int]:
    """Returns a summary of unresolved realizations."""
    state_dir = Path("state")
    unresolved_file = state_dir / "unresolved_realizations.json"
    if not unresolved_file.exists():
        return {}
    with open(unresolved_file, "r") as f:
        data = json.load(f)
    summary = {}
    for item in data:
        reason = item["reason"]
        summary[reason] = summary.get(reason, 0) + 1
    return summary

def get_unresolved_by_delta(delta: float) -> List[int]:
    """Returns a list of unresolved realization IDs for a given delta."""
    state_dir = Path("state")
    unresolved_file = state_dir / "unresolved_realizations.json"
    if not unresolved_file.exists():
        return []
    with open(unresolved_file, "r") as f:
        data = json.load(f)
    unresolved_ids = []
    for item in data:
        if item.get("delta") == delta:
            unresolved_ids.append(item["realization_id"])
    return unresolved_ids

def get_unresolved_by_reason(reason: str) -> List[int]:
    """Returns a list of unresolved realization IDs for a given reason."""
    state_dir = Path("state")
    unresolved_file = state_dir / "unresolved_realizations.json"
    if not unresolved_file.exists():
        return []
    with open(unresolved_file, "r") as f:
        data = json.load(f)
    unresolved_ids = []
    for item in data:
        if item["reason"] == reason:
            unresolved_ids.append(item["realization_id"])
    return unresolved_ids

def clear_unresolved_log() -> None:
    """Clears the unresolved realizations log."""
    state_dir = Path("state")
    unresolved_file = state_dir / "unresolved_realizations.json"
    if unresolved_file.exists():
        unresolved_file.unlink()
