import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import fcntl

# Configuration
LOG_FILE_PATH = Path("data/run_log.json")

# Ensure data directory exists
LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

def init_logging() -> None:
    """Initialize the logging infrastructure.
    
    Creates an empty run_log.json if it does not exist.
    Sets up standard logging to console.
    """
    if not LOG_FILE_PATH.exists():
        with open(LOG_FILE_PATH, 'w') as f:
            json.dump([], f)
    
    # Configure standard logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def _load_log() -> List[Dict[str, Any]]:
    """Load the current run log from disk."""
    if not LOG_FILE_PATH.exists():
        return []
    try:
        with open(LOG_FILE_PATH, 'r') as f:
            content = f.read().strip()
            if not content:
                return []
            return json.loads(content)
    except json.JSONDecodeError:
        logging.error(f"Failed to decode {LOG_FILE_PATH}. Returning empty log.")
        return []

def _save_log(log_data: List[Dict[str, Any]]) -> None:
    """Save the run log to disk with file locking for safety."""
    with open(LOG_FILE_PATH, 'w') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            json.dump(log_data, f, indent=2)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

def log_metric(event: Dict[str, Any]) -> None:
    """Append a validated entry to the run log.
    
    Args:
        event: Dictionary containing log entry data.
               Required keys: timestamp, event_type, run_id, seed, status, duration_seconds.
    
    Raises:
        ValueError: If required keys are missing or types are invalid.
    """
    required_keys = {'timestamp', 'event_type', 'run_id', 'seed', 'status', 'duration_seconds'}
    if not required_keys.issubset(event.keys()):
        missing = required_keys - set(event.keys())
        raise ValueError(f"Log entry missing required keys: {missing}")
    
    # Validate event_type enum
    valid_event_types = {'graph_generated', 'simulation_start', 'simulation_end', 'divergence_detected', 'timeout_reached'}
    if event['event_type'] not in valid_event_types:
        raise ValueError(f"Invalid event_type: {event['event_type']}. Must be one of {valid_event_types}")
    
    # Validate types
    if not isinstance(event['timestamp'], str):
        raise ValueError("timestamp must be a string (ISO 8601)")
    if not isinstance(event['run_id'], str):
        raise ValueError("run_id must be a string")
    if not isinstance(event['seed'], int):
        raise ValueError("seed must be an integer")
    if not isinstance(event['status'], str):
        raise ValueError("status must be a string")
    if not isinstance(event['duration_seconds'], (int, float)):
        raise ValueError("duration_seconds must be a number")

    # Load existing log, append, and save
    log_data = _load_log()
    log_data.append(event)
    _save_log(log_data)

    logging.info(f"Logged event: {event['event_type']} for run {event['run_id']}")

def get_run_log() -> List[Dict[str, Any]]:
    """Retrieve the full run log."""
    return _load_log()
