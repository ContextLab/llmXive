import logging
import sys
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pathlib import Path

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

_logger_instance: Optional[logging.Logger] = None
_log_file_path: Optional[Path] = None

def configure_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> None:
    """Configure the root logger."""
    global _logger_instance, _log_file_path
    
    if _logger_instance is not None:
        return

    _logger_instance = logging.getLogger('llmXive')
    _logger_instance.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    _logger_instance.addHandler(console_handler)

    if log_file:
        _log_file_path = Path(log_file)
        _log_file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        _logger_instance.addHandler(file_handler)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance, optionally with a specific name."""
    if _logger_instance is None:
        configure_logging()
    if name:
        return _logger_instance.getChild(name)
    return _logger_instance

def heartbeat(node_id: str, event_type: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Log a heartbeat event."""
    logger = get_logger()
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "node_id": node_id,
        "event_type": event_type,
        "details": details or {}
    }
    logger.info(json.dumps(log_entry))

def get_log_file_path() -> Optional[Path]:
    """Return the path to the log file if configured."""
    return _log_file_path
