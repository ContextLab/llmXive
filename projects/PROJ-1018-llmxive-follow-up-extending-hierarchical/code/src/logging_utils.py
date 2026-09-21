import json
import logging
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import hashlib
import os

# Global logger instance to be reused
_logger: Optional[logging.Logger] = None

# Attempt to read version hash from git or fallback to a static hash of the project root
def _get_version_hash() -> str:
    """
    Attempts to retrieve the current git commit hash.
    Falls back to a hash of the project root path if git is unavailable.
    """
    try:
        # Try to get git commit hash
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        return result.stdout.strip()
    except Exception:
        # Fallback: deterministic hash based on project root
        root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return hashlib.sha256(root_path.encode('utf-8')).hexdigest()[:8]

VERSION_HASH = _get_version_hash()

class JSONFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs log records as JSON lines.
    Expected fields: timestamp, level, message, version_hash.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "version_hash": VERSION_HASH
        }

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include extra fields if provided
        if hasattr(record, 'extra_data') and isinstance(record.extra_data, dict):
            log_data.update(record.extra_data)

        return json.dumps(log_data)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves or creates a logger configured for JSON line output.
    The logger writes to stdout.
    """
    global _logger
    
    # If a specific name is requested and it's not the global one, handle it
    if name is not None:
        logger = logging.getLogger(name)
    else:
        if _logger is None:
            _logger = logging.getLogger("llmxive")
            _logger.setLevel(logging.INFO)
            
            # Prevent adding handlers multiple times
            if not _logger.handlers:
                handler = logging.StreamHandler(sys.stdout)
                handler.setFormatter(JSONFormatter())
                _logger.addHandler(handler)
        
        return _logger

    # Ensure the specific logger also has the JSON handler if it doesn't
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger

def log_version_info() -> None:
    """
    Logs the current version hash to help with reproducibility tracking.
    """
    logger = get_logger()
    logger.info(f"Initialized logger with version_hash: {VERSION_HASH}")