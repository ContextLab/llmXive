import logging
import sys
import json
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

# Custom Exceptions
class DataAvailabilityError(Exception):
    """Raised when real data is unavailable or incomplete."""
    pass

class VoronoiFailure(Exception):
    """Raised when Voronoi tessellation fails."""
    pass

# Logger Setup
def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def log_audit_event(event_type: str, event_name: str, details: Dict[str, Any]) -> None:
    """
    Logs an event to data/audit_log.json.
    Creates the file and directory if they don't exist.
    """
    audit_path = Path("data/audit_log.json")
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    event = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "name": event_name,
        "details": details
    }

    # Read existing log if exists
    log_data = []
    if audit_path.exists():
        try:
            with open(audit_path, 'r') as f:
                content = f.read().strip()
                if content:
                    log_data = json.loads(content)
        except json.JSONDecodeError:
            log_data = []

    log_data.append(event)

    # Write back
    with open(audit_path, 'w') as f:
        json.dump(log_data, f, indent=2)

# Ensure data directory exists for audit log
Path("data").mkdir(parents=True, exist_ok=True)
