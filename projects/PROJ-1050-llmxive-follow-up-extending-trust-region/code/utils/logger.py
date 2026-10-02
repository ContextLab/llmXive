"""
Logging Configuration and Utilities.

Sets up logging to both console and file, with rotation and specific formatting.
"""
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

_logger_instance = None
_log_path = None

def setup_logging(log_path: Optional[Path] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure the root logger and create a project-specific logger.
    
    Args:
        log_path: Path to the log file. If None, uses default data/raw/ path.
        level: Logging level.
    """
    global _logger_instance, _log_path

    if _logger_instance:
        return _logger_instance

    if log_path is None:
        log_path = Path("data/raw/app.log")
    
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _log_path = log_path

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers = []

    # File handler
    fh = logging.FileHandler(str(log_path))
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(logging.Formatter(
        '%(levelname)s - %(message)s'
    ))

    root_logger.addHandler(fh)
    root_logger.addHandler(ch)

    _logger_instance = logging.getLogger("llmXive")
    return _logger_instance

def get_logger(name: str = "llmXive") -> logging.Logger:
    """Get a logger instance."""
    if not _logger_instance:
        setup_logging()
    return logging.getLogger(name)

def get_log_path() -> Optional[Path]:
    """Get the current log file path."""
    return _log_path

def export_log_summary(output_path: Path):
    """Export a summary of logs to a file."""
    if not _log_path or not _log_path.exists():
        return
    
    # Simple summary: count lines
    with open(_log_path, 'r') as f:
        lines = f.readlines()
    
    with open(output_path, 'w') as f:
        f.write(f"Log Summary: {_log_path}\n")
        f.write(f"Total Lines: {len(lines)}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
