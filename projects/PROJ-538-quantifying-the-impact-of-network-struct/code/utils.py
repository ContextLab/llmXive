import logging
import sys
import json
from typing import Optional
from pathlib import Path
from datetime import datetime
import threading

from .config import config

# Custom Exceptions
class DataAvailabilityError(Exception):
    """Raised when required real data is missing or incomplete."""
    pass

class VoronoiFailure(Exception):
    """Raised when Voronoi tessellation fails (e.g., collinear points)."""
    pass

# Thread-safe logger instance
_logger_instance: Optional[logging.Logger] = None
_logger_lock = threading.Lock()
_audit_handler: Optional[logging.Handler] = None

def _ensure_audit_handler() -> logging.Handler:
    """Creates or retrieves the file handler for audit logging."""
    global _audit_handler
    if _audit_handler is None:
        audit_path = Path(config.data_dir) / "audit_log.json"
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        
        class JSONAuditHandler(logging.Handler):
            def __init__(self, filepath: Path):
                super().__init__()
                self.filepath = filepath
                self._lock = threading.Lock()
            
            def emit(self, record):
                try:
                    log_entry = {
                        "timestamp": datetime.utcnow().isoformat(),
                        "level": record.levelname,
                        "module": record.module,
                        "function": record.funcName,
                        "message": record.getMessage(),
                        "extra": record.__dict__.get("extra", {})
                    }
                    # Append mode for JSONL
                    with self._lock:
                        with open(self.filepath, "a", encoding="utf-8") as f:
                            f.write(json.dumps(log_entry) + "\n")
                except Exception:
                    self.handleError(record)

        _audit_handler = JSONAuditHandler(audit_path)
        _audit_handler.setLevel(logging.INFO)
        _audit_handler.setFormatter(logging.Formatter("%(message)s"))
    return _audit_handler

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Returns a configured logger that writes to both console and data/audit_log.json.
    Uses a singleton pattern to ensure consistent configuration across the project.
    """
    global _logger_instance
    
    with _logger_lock:
        if _logger_instance is None:
            _logger_instance = logging.getLogger(name)
            _logger_instance.setLevel(logging.DEBUG)
            
            # Prevent duplicate handlers if called multiple times
            if not _logger_instance.handlers:
                # Console Handler
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(logging.INFO)
                console_format = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
                console_handler.setFormatter(console_format)
                _logger_instance.addHandler(console_handler)

                # Audit File Handler
                audit_handler = _ensure_audit_handler()
                _logger_instance.addHandler(audit_handler)

        return _logger_instance

def log_audit_event(event_type: str, details: dict, logger: Optional[logging.Logger] = None):
    """
    Convenience wrapper to log structured audit events.
    Ensures the event is written to the JSON audit log.
    """
    if logger is None:
        logger = get_logger()
    
    # Create a custom log record with extra details
    logger.info(
        f"Audit Event: {event_type}",
        extra={"extra": {"event_type": event_type, **details}}
    )
