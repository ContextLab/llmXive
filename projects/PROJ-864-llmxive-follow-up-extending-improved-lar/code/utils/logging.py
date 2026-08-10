"""
Logging infrastructure for the llmXive project.
Provides a centralized logger configuration.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

_logger: Optional[logging.Logger] = None
_log_file: Optional[Path] = None

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    project_root: Optional[Path] = None
) -> logging.Logger:
    """
    Configures the global logger for the project.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to a log file. If None, logs to console only.
        project_root: Root of the project. Defaults to inferred path.
    
    Returns:
        The configured logger instance.
    """
    global _logger, _log_file
    
    if _logger is not None:
        return _logger

    # Infer project root if not provided
    if project_root is None:
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent

    _logger = logging.getLogger("llmXive")
    _logger.setLevel(level)
    _logger.handlers = [] # Clear existing handlers

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    _logger.addHandler(ch)

    # File Handler
    if log_file is None:
        logs_dir = project_root / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = logs_dir / f"run_{timestamp}.log"
    else:
        log_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        fh = logging.FileHandler(str(log_file))
        fh.setLevel(level)
        fh.setFormatter(formatter)
        _logger.addHandler(fh)
        _log_file = log_file
        _logger.info(f"Logging initialized. File: {log_file}")
    except Exception as e:
        _logger.error(f"Failed to create log file {log_file}: {e}")

    return _logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves the global logger or a child logger.
    """
    if _logger is None:
        # Auto-setup if not initialized
        setup_logging()
    
    if name:
        return _logger.getChild(name)
    return _logger

def reset_logging():
    """Resets the global logger state."""
    global _logger, _log_file
    _logger = None
    _log_file = None

# Convenience functions
def debug(msg: str):
    if _logger: _logger.debug(msg)

def info(msg: str):
    if _logger: _logger.info(msg)

def warning(msg: str):
    if _logger: _logger.warning(msg)

def error(msg: str):
    if _logger: _logger.error(msg)

def critical(msg: str):
    if _logger: _logger.critical(msg)

def exception(msg: str):
    if _logger: _logger.exception(msg)
