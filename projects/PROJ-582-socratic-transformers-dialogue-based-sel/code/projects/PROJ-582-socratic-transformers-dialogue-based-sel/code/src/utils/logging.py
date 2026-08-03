"""
Structured logging utility for Socratic Transformers.
Handles degenerate dialogue events as JSON lines.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from src.utils.config import get_config


class SocraticLogger:
    """
    Custom logger that outputs structured JSON logs for degenerate events.
    """
    def __init__(self, name: str, log_dir: Optional[Path] = None):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        if not self.logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        if log_dir is None:
            config = get_config()
            log_dir = Path(config.log_dir)
        
        log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = log_dir / f"{name}_events.jsonl"
        
        self.file_handler = logging.FileHandler(self.log_file)
        self.file_handler.setLevel(logging.DEBUG)
        self.file_handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(self.file_handler)

    def log_event(self, event_type: str, data: Dict[str, Any], level: str = "INFO"):
        """Log a structured event as JSON."""
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "logger": self.name,
            "data": data
        }
        
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.log(log_level, json.dumps(record))

    def info(self, msg: str):
        self.logger.info(msg)

    def debug(self, msg: str):
        self.logger.debug(msg)

    def warning(self, msg: str):
        self.logger.warning(msg)

    def error(self, msg: str):
        self.logger.error(msg)


_logger_instance: Optional[SocraticLogger] = None

def get_logger(name: str = "socratic") -> SocraticLogger:
    """Get or create a SocraticLogger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = SocraticLogger(name)
    # In a multi-process scenario, we might want per-name loggers
    # For now, return a new instance per name to be safe
    return SocraticLogger(name)
