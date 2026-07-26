import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

LOG_FILE_PATH = "data/run_log.json"

def _ensure_log_file():
    """Ensure the log file exists and is a valid JSON array."""
    path = Path(LOG_FILE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with open(path, 'w') as f:
            json.dump([], f)
    else:
        try:
            with open(path, 'r') as f:
                content = f.read().strip()
                if not content:
                    with open(path, 'w') as wf:
                        json.dump([], wf)
                else:
                    json.loads(content) # Validate
        except (json.JSONDecodeError, FileNotFoundError):
            with open(path, 'w') as f:
                json.dump([], f)

def append_to_log(entry: Dict[str, Any]):
    """Append an entry to the run log."""
    _ensure_log_file()
    path = Path(LOG_FILE_PATH)
    try:
        with open(path, 'r') as f:
            logs = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        logs = []

    # Ensure entry has timestamp if missing
    if 'timestamp' not in entry:
        entry['timestamp'] = datetime.now().isoformat()

    logs.append(entry)

    with open(path, 'w') as f:
        json.dump(logs, f, indent=2)

def get_run_log() -> List[Dict[str, Any]]:
    """Read the entire run log."""
    _ensure_log_file()
    path = Path(LOG_FILE_PATH)
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def log_run(event_type: str, run_id: str, seed: int, status: str = "SUCCESS", duration_ms: Optional[int] = None):
    """Convenience wrapper for logging run events."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "run_id": run_id,
        "seed": seed,
        "status": status,
        "duration_ms": duration_ms
    }
    append_to_log(entry)

def log_metric(name: str, value: Any, run_id: str):
    """Log a specific metric value."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": "metric",
        "run_id": run_id,
        "metric_name": name,
        "metric_value": value
    }
    append_to_log(entry)

# Initialize logging for the module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
