"""
Structured logging utility for handling degenerate dialogue events as JSON lines.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src.utils.config import get_config, ensure_directories


class SocraticLogger:
    """
    A custom logger that outputs structured JSON lines for degenerate dialogue events.
    
    This logger is designed to handle the specific logging needs of the Socratic
    Transformers project, ensuring that all events are serialized as JSON for
    easy parsing and analysis.
    """
    
    def __init__(self, name: str, level: int = logging.INFO, log_file: Optional[Path] = None):
        """
        Initialize the SocraticLogger.
        
        Args:
            name: Name of the logger.
            level: Logging level.
            log_file: Optional path to a log file. If None, logs to stdout.
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatter for JSON output
        self.json_formatter = SocraticJSONFormatter()
        
        # Add console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self.json_formatter)
        self.logger.addHandler(console_handler)
        
        # Add file handler if log_file is provided
        if log_file:
            ensure_directories()  # Ensure directories exist
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(self.json_formatter)
            self.logger.addHandler(file_handler)
    
    def _log(self, level: int, message: str, extra: Optional[Dict[str, Any]] = None):
        """
        Internal logging method that structures the log entry as JSON.
        
        Args:
            level: Logging level.
            message: Log message.
            extra: Additional context data to include in the log entry.
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "logger": self.name,
            "level": logging.getLevelName(level),
            "message": message,
        }
        if extra:
            entry["context"] = extra
        
        # Use the logger's internal methods to avoid recursion
        # We pass the JSON string directly to avoid double formatting
        self.logger.log(level, json.dumps(entry))
    
    def debug(self, message: str, **kwargs):
        """Log a debug message."""
        self._log(logging.DEBUG, message, kwargs)
    
    def info(self, message: str, **kwargs):
        """Log an info message."""
        self._log(logging.INFO, message, kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log a warning message."""
        self._log(logging.WARNING, message, kwargs)
    
    def error(self, message: str, **kwargs):
        """Log an error message."""
        self._log(logging.ERROR, message, kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log a critical message."""
        self._log(logging.CRITICAL, message, kwargs)
    
    def log_dialogue_event(self, event_type: str, data: Dict[str, Any]):
        """
        Log a specific dialogue event (e.g., question, answer, critique).
        
        Args:
            event_type: Type of event (e.g., "question_generated", "critique_produced").
            data: Dictionary containing event-specific data.
        """
        self.info(f"Dialogue Event: {event_type}", event_type=event_type, **data)


class SocraticJSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON lines.
    """
    
    def format(self, record):
        """
        Format the log record as a JSON string.
        
        Args:
            record: The log record.
            
        Returns:
            A JSON string representation of the log record.
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "logger": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, "context"):
            log_entry["context"] = record.context
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


# Global logger instance (lazy initialization)
_global_logger: Optional[SocraticLogger] = None

def get_logger(name: str = "socratic", log_file: Optional[Path] = None) -> SocraticLogger:
    """
    Get or create a SocraticLogger instance.
    
    Args:
        name: Name of the logger.
        log_file: Optional path to a log file.
        
    Returns:
        A SocraticLogger instance.
    """
    global _global_logger
    if _global_logger is None or name != _global_logger.name:
        config = get_config()
        if log_file is None:
            # Default log file in logs directory
            log_file = config.logs_dir / f"{name}.log"
        _global_logger = SocraticLogger(name, log_file=log_file)
    return _global_logger
