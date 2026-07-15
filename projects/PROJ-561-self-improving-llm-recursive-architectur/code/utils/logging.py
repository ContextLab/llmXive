"""
utils/logging.py

Structured cycle logging and checkpointing for the self-improving LLM pipeline.
Provides deterministic, JSON-based logging of cycle metrics and state snapshots
to support reproducibility and trajectory analysis.
"""

import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import threading

from config import PathConfig, get_config_summary


# Global lock for thread-safe logging
_log_lock = threading.Lock()

# Configure standard logger
_logger = logging.getLogger("llmxive.cycle_logger")
_logger.setLevel(logging.INFO)
if not _logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    _logger.addHandler(handler)


def get_log_path() -> Path:
    """
    Returns the path to the main trajectory log file based on PathConfig.
    """
    config = get_config_summary()
    # PathConfig is usually instantiated in config.py, but we access via helper
    # to ensure we get the active configuration.
    # Assuming PathConfig has a 'results_dir' attribute.
    # Fallback if config summary doesn't expose it directly:
    if hasattr(config, 'results_dir'):
        base_dir = config.results_dir
    else:
        # Fallback to standard project structure if config is minimal
        base_dir = "results"

    log_file = Path(base_dir) / "trajectory.json"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    return log_file


def init_cycle_logger(cycle_id: int) -> Dict[str, Any]:
    """
    Initializes a new log entry structure for a specific cycle.
    Returns the initial log dictionary.
    """
    entry = {
        "cycle_id": cycle_id,
        "start_time_iso": datetime.utcnow().isoformat(),
        "start_timestamp": time.time(),
        "status": "started",
        "metrics": {},
        "artifacts": [],
        "errors": []
    }
    _logger.info(f"Initialized log for cycle {cycle_id}")
    return entry


def update_cycle_log(
    cycle_id: int,
    metrics: Optional[Dict[str, Any]] = None,
    artifacts: Optional[List[str]] = None,
    status: Optional[str] = None,
    error: Optional[str] = None
) -> None:
    """
    Updates the persistent log file for a given cycle with new metrics, artifacts,
    status, or errors. Uses a lock to ensure thread safety.
    """
    log_path = get_log_path()
    log_data = []

    # Load existing data if file exists
    if log_path.exists():
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_data = json.load(f)
        except json.JSONDecodeError:
            _logger.warning(f"Corrupt log file at {log_path}, initializing fresh.")
            log_data = []

    # Ensure log_data is a list
    if not isinstance(log_data, list):
        log_data = [log_data] if log_data else []

    # Find existing entry for this cycle or create new
    entry_index = None
    for i, entry in enumerate(log_data):
        if entry.get("cycle_id") == cycle_id:
            entry_index = i
            break

    if entry_index is None:
        # Create new entry
        new_entry = {
            "cycle_id": cycle_id,
            "start_time_iso": datetime.utcnow().isoformat(),
            "start_timestamp": time.time(),
            "status": "running",
            "metrics": {},
            "artifacts": [],
            "errors": []
        }
        log_data.append(new_entry)
        entry_index = len(log_data) - 1

    # Update the entry
    entry = log_data[entry_index]

    if metrics:
        entry["metrics"].update(metrics)
    
    if artifacts:
        # Append unique artifacts
        existing = set(entry.get("artifacts", []))
        for art in artifacts:
            if art not in existing:
                entry["artifacts"].append(art)
                existing.add(art)

    if status:
        entry["status"] = status
        if status == "completed":
            entry["end_time_iso"] = datetime.utcnow().isoformat()
            entry["end_timestamp"] = time.time()
            duration = entry.get("end_timestamp", 0) - entry.get("start_timestamp", 0)
            entry["duration_seconds"] = duration
        elif status == "failed":
            entry["end_time_iso"] = datetime.utcnow().isoformat()
            entry["end_timestamp"] = time.time()

    if error:
        entry["errors"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "message": error
        })
        entry["status"] = "failed"

    # Write back atomically
    with _log_lock:
        temp_path = str(log_path) + ".tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, default=str)
        os.replace(temp_path, log_path)

    _logger.info(f"Updated log for cycle {cycle_id} with status: {status}")


def checkpoint_model_state(
    cycle_id: int,
    model_path: str,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Records a checkpoint of the model state in the log.
    Returns the relative path to the checkpoint.
    """
    # Ensure the path is recorded as an artifact
    rel_path = os.path.relpath(model_path, start=get_config_summary().results_dir if hasattr(get_config_summary(), 'results_dir') else "results")
    update_cycle_log(
        cycle_id,
        artifacts=[rel_path],
        metrics={"checkpoint_path": rel_path}
    )
    if metadata:
        update_cycle_log(cycle_id, metrics=metadata)
    return rel_path


def log_cycle_summary(cycle_id: int, summary: Dict[str, Any]) -> None:
    """
    Logs a final summary for a cycle, typically containing aggregated metrics
    and final status.
    """
    update_cycle_log(cycle_id, metrics=summary, status="completed")
    _logger.info(f"Cycle {cycle_id} summary logged: {summary}")


def get_cycle_history() -> List[Dict[str, Any]]:
    """
    Reads and returns the full history of cycles from the log file.
    """
    log_path = get_log_path()
    if not log_path.exists():
        return []
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        _logger.error(f"Failed to parse log file: {log_path}")
        return []