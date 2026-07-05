"""
Logging infrastructure for the llmXive automated science pipeline.

Captures seeds, parameters, and runtime metrics, writing to data/run_log.json.
This module provides a structured logging interface that appends run metadata
to a persistent JSON log file.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Project root relative to this file (code/src/utils/ -> ../.. -> project root)
# Assuming standard layout: project_root/code/src/utils/logging.py
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_DATA_DIR = _PROJECT_ROOT / "data"
_LOG_FILE_PATH = _DATA_DIR / "run_log.json"

# Ensure data directory exists
_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_existing_log() -> List[Dict[str, Any]]:
    """Load existing log entries from disk, or return empty list if file doesn't exist."""
    if not _LOG_FILE_PATH.exists():
        return []
    try:
        with open(_LOG_FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return []
            data = json.loads(content)
            if isinstance(data, list):
                return data
            # Handle case where file might contain a single object (legacy or error)
            return [data] if isinstance(data, dict) else []
    except (json.JSONDecodeError, IOError):
        return []


def _save_log(entries: List[Dict[str, Any]]) -> None:
    """Save log entries to disk with atomic write pattern (write to temp, then rename)."""
    temp_path = _LOG_FILE_PATH.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, default=str)
    os.replace(temp_path, _LOG_FILE_PATH)


def log_run(
    seed: Optional[int] = None,
    parameters: Optional[Dict[str, Any]] = None,
    metrics: Optional[Dict[str, Any]] = None,
    run_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Log a run's metadata to data/run_log.json.
    
    Args:
        seed: Random seed used for the run.
        parameters: Dictionary of configuration parameters used.
        metrics: Dictionary of runtime metrics (e.g., duration, memory).
        run_id: Unique identifier for the run. If None, generated automatically.
        extra: Additional metadata to include.
    
    Returns:
        The log entry that was written.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    # Generate run_id if not provided
    if run_id is None:
        run_id = f"run_{timestamp.replace(':', '-').replace('.', '_')}"
    
    entry = {
        "timestamp": timestamp,
        "run_id": run_id,
        "seed": seed,
        "parameters": parameters or {},
        "metrics": metrics or {},
    }
    
    if extra:
        entry["extra"] = extra
    
    # Load existing, append, save
    entries = _load_existing_log()
    entries.append(entry)
    _save_log(entries)
    
    return entry


def log_metric(
    metric_name: str,
    value: Union[int, float, str],
    run_id: Optional[str] = None,
    seed: Optional[int] = None,
    parameters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Log a single metric, optionally creating a new run entry if run_id is provided.
    
    If run_id is None, this function will append the metric to the most recent
    run entry (or create a new one if none exist).
    
    Args:
        metric_name: Name of the metric.
        value: Value of the metric.
        run_id: Optional run ID to associate the metric with.
        seed: Optional seed for the run.
        parameters: Optional parameters for the run.
    
    Returns:
        The updated run entry.
    """
    entries = _load_existing_log()
    
    # Find the target entry
    target_idx = None
    if run_id:
        for i, entry in enumerate(entries):
            if entry.get("run_id") == run_id:
                target_idx = i
                break
        if target_idx is None:
            # Create new entry
            target_idx = len(entries)
            new_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "run_id": run_id,
                "seed": seed,
                "parameters": parameters or {},
                "metrics": {},
            }
            entries.append(new_entry)
    else:
        # Append to last entry or create new
        if entries:
            target_idx = len(entries) - 1
        else:
            target_idx = len(entries)
            new_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "run_id": f"run_{datetime.utcnow().isoformat().replace(':', '-').replace('.', '_')}",
                "seed": seed,
                "parameters": parameters or {},
                "metrics": {},
            }
            entries.append(new_entry)
    
    # Update metrics
    entries[target_idx]["metrics"][metric_name] = value
    
    _save_log(entries)
    return entries[target_idx]


def get_run_log() -> List[Dict[str, Any]]:
    """
    Retrieve the entire run log.
    
    Returns:
        List of all log entries.
    """
    return _load_existing_log()


def clear_run_log() -> None:
    """
    Clear the run log file.
    
    WARNING: This deletes all historical run data.
    """
    if _LOG_FILE_PATH.exists():
        _LOG_FILE_PATH.unlink()
