import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from .config import get_config, get_data_path

# Global logger instance
_logger: Optional[logging.Logger] = None
_log_level: int = logging.INFO

class PipelineLogger:
    """
    A wrapper around Python's logging module tailored for the plant defense pipeline.
    Handles file rotation, structured logging, and integration with provenance tracking.
    """

    def __init__(self, name: str = "plant_defense_pipeline"):
        self.name = name
        self.logger = logging.getLogger(name)
        self._handlers_added = False

    def setup(self, log_file: Optional[str] = None, level: int = logging.INFO):
        """
        Configures the logger with console and file handlers.
        
        Args:
            log_file: Path to the log file. If None, defaults to data/logs/pipeline.log
            level: Logging level (e.g., logging.DEBUG, logging.INFO)
        """
        global _log_level
        _log_level = level
        self.logger.setLevel(level)

        if self._handlers_added:
            return

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File Handler
        if log_file is None:
            try:
                data_root = get_data_path()
                log_dir = Path(data_root) / "logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                log_file = str(log_dir / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
            except Exception:
                # Fallback if config not ready yet
                log_file = "pipeline.log"

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        self._handlers_added = True

    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, **kwargs)

    def info(self, msg: str, **kwargs):
        self.logger.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self.logger.error(msg, **kwargs)

    def critical(self, msg: str, **kwargs):
        self.logger.critical(msg, **kwargs)

    def log_provenance_event(self, event_type: str, details: Dict[str, Any]):
        """
        Logs a structured provenance event.
        """
        msg = f"PROVENANCE | {event_type} | {details}"
        self.logger.info(msg)

def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> PipelineLogger:
    """
    Initializes the global pipeline logger.
    
    Args:
        log_file: Optional path to log file.
        level: Logging level.
    
    Returns:
        Configured PipelineLogger instance.
    """
    global _logger
    if _logger is None:
        _logger = PipelineLogger()
        _logger.setup(log_file, level)
    else:
        _logger.setup(log_file, level)
    return _logger

def set_log_level(level: int):
    """
    Updates the global log level and propagates to existing handlers.
    """
    global _log_level, _logger
    _log_level = level
    if _logger:
        _logger.logger.setLevel(level)
        for handler in _logger.logger.handlers:
            handler.setLevel(level)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves the configured logger.
    
    Args:
        name: Optional sub-logger name (e.g., 'src.data.download').
    
    Returns:
        A logging.Logger instance.
    """
    if _logger is None:
        # Initialize with defaults if not explicitly set up
        setup_logging()
    
    if name:
        return _logger.logger.getChild(name)
    return _logger.logger
