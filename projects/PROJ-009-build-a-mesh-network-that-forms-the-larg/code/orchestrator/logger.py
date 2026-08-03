"""
Logging infrastructure for the project.
Captures wall-clock timestamps and heartbeat events.
"""
import logging
import sys
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pathlib import Path

_logger_instance: Optional[logging.Logger] = None

def configure_logging(log_file: Optional[str] = None, level: int = logging.INFO):
    """Configure the root logger."""
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = logging.getLogger("llmXive")
        _logger_instance.setLevel(level)
        
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        _logger_instance.addHandler(ch)
        
        # File handler
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(level)
            fh.setFormatter(formatter)
            _logger_instance.addHandler(fh)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    if _logger_instance is None:
        configure_logging()
    return logging.getLogger(f"llmXive.{name}")

def heartbeat(node_id: str, event: str):
    """Log a heartbeat event."""
    logger = get_logger("heartbeat")
    logger.info(json.dumps({
        "type": "heartbeat",
        "node_id": node_id,
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }))

def get_log_file_path() -> Optional[str]:
    """Return the path to the log file if configured."""
    # Implementation to retrieve log file path
    return None
