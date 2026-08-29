import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Constants
LOG_FILE_PATH = "data/run_log.json"

# Ensure log directory exists
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

def init_logging() -> None:
    """Initialize logging infrastructure and create empty log file if needed."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('data/run.log')
        ]
    )
    if not os.path.exists(LOG_FILE_PATH):
        with open(LOG_FILE_PATH, 'w') as f:
            json.dump([], f)

def load_existing_log() -> List[Dict[str, Any]]:
    """Load the existing log entries from the JSON file."""
    if not os.path.exists(LOG_FILE_PATH):
        return []
    try:
        with open(LOG_FILE_PATH, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_log(log_entries: List[Dict[str, Any]]) -> None:
    """Save log entries to the JSON file."""
    with open(LOG_FILE_PATH, 'w') as f:
        json.dump(log_entries, f, indent=2)

def log_metric(event: Dict[str, Any]) -> None:
    """Append a metric entry to the run log.
    
    Args:
        event: Dictionary containing event data. Expected keys:
               timestamp (ISO 8601), event_type, run_id, seed, status, duration_seconds.
    """
    log_entries = load_existing_log()
    
    # Ensure required fields exist
    required_fields = {'timestamp', 'event_type', 'run_id', 'seed', 'status', 'duration_seconds'}
    missing_fields = required_fields - set(event.keys())
    if missing_fields:
        raise ValueError(f"Missing required fields in log entry: {missing_fields}")
    
    log_entries.append(event)
    save_log(log_entries)

def log_run(event_type: str, run_id: str, seed: int, status: str, duration_seconds: float, **kwargs) -> None:
    """Convenience wrapper to log a full run event with standardized fields.
    
    Args:
        event_type: Type of event (e.g., 'graph_generated', 'simulation_start', 'simulation_end')
        run_id: Unique identifier for the run
        seed: Random seed used
        status: Status of the event (e.g., 'success', 'failed', 'timeout_reached')
        duration_seconds: Duration of the event in seconds
        **kwargs: Additional fields to include in the log entry
    """
    event = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event_type': event_type,
        'run_id': run_id,
        'seed': seed,
        'status': status,
        'duration_seconds': duration_seconds
    }
    event.update(kwargs)
    log_metric(event)

def get_run_log() -> List[Dict[str, Any]]:
    """Retrieve the current run log."""
    return load_existing_log()
