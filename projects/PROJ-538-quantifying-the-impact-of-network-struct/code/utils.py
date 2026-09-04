import logging
import sys
import json
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
AUDIT_LOG_PATH = DATA_DIR / "audit_log.json"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Custom Exceptions
class DataAvailabilityError(Exception):
    """Raised when required real data is missing or incomplete."""
    pass

class VoronoiFailure(Exception):
    """Raised when Voronoi tessellation fails."""
    pass

# Logger configuration
_logger: Optional[logging.Logger] = None

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Returns a configured logger that outputs to both console and a file.
    Singleton pattern to ensure consistent configuration.
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger(name)
        if _logger.handlers:
            return _logger

        _logger.setLevel(logging.INFO)

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)

        # File Handler (for detailed audit logs if needed, though we use JSON for audit)
        # We log general info to a text file for debugging, but audit events go to JSON
        file_handler = logging.FileHandler(PROJECT_ROOT / "logs" / "app.log")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)

        # Ensure logs dir exists
        (PROJECT_ROOT / "logs").mkdir(parents=True, exist_ok=True)

        _logger.addHandler(console_handler)
        _logger.addHandler(file_handler)
        _logger.propagate = False

    return _logger

def log_audit_event(event_type: str, details: Dict[str, Any], status: str = "INFO") -> None:
    """
    Appends an audit event to the JSON audit log.
    Thread-safe append using standard file I/O (sufficient for single-process execution).
    """
    logger = get_logger("audit")
    timestamp = datetime.utcnow().isoformat() + "Z"

    audit_entry = {
        "timestamp": timestamp,
        "event_type": event_type,
        "status": status,
        "details": details
    }

    logger.info(f"Audit Event: {event_type} - {status}")

    # Read existing log if it exists
    log_data = []
    if AUDIT_LOG_PATH.exists():
        try:
            with open(AUDIT_LOG_PATH, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    # Handle potential newline-separated JSON or array JSON
                    if content.startswith('['):
                        log_data = json.loads(content)
                    else:
                        # Line-delimited JSON
                        for line in content.splitlines():
                            if line.strip():
                                log_data.append(json.loads(line))
        except json.JSONDecodeError:
            logger.warning("Existing audit log is malformed. Starting fresh.")
            log_data = []

    # Append new entry
    log_data.append(audit_entry)

    # Write back as JSON Lines (newline-delimited JSON) for robustness
    # This avoids loading the whole file into memory if it gets huge
    with open(AUDIT_LOG_PATH, 'w', encoding='utf-8') as f:
        for entry in log_data:
            f.write(json.dumps(entry) + '\n')

# Initialize logger immediately for module-level usage
_logger = get_logger()
