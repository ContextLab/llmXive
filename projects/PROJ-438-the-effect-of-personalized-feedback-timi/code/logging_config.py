"""
logging_config.py

Sets up logging infrastructure for reproducible audit trails.
Provides a centralized logger configuration to ensure consistent formatting
and output destinations (console and file) across the entire pipeline.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Import config to determine log file paths and levels
# Note: We assume config.py is available as per T007 completion
try:
    from config import load_config, get_config_value
except ImportError:
    # Fallback if config is not yet available during early import tests
    # In a real run, config will be present.
    load_config = None
    get_config_value = None

# Global logger instance cache to avoid re-configuration
_loggers = {}
_default_log_file = None
_default_level = logging.INFO

def _get_project_root() -> Path:
    """
    Determines the project root directory relative to this file.
    Assumes structure: code/logging_config.py -> project root is 2 levels up.
    """
    current_file = Path(__file__).resolve()
    # Assuming the file is at: projects/PROJ-.../code/logging_config.py
    # We want to go up to the project root: projects/PROJ-.../
    return current_file.parent.parent

def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    log_dir: Optional[str] = None
) -> logging.Logger:
    """
    Configures a logger with console and optional file output.

    Args:
        name: Name of the logger (e.g., "download_data", "preprocess").
        log_file: Optional specific log file path. If None, uses default.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_dir: Optional directory for log files. Defaults to project root logs/.

    Returns:
        Configured logging.Logger instance.
    """
    global _default_log_file, _default_level

    # Cache key
    if name in _loggers and _loggers[name].level == level:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers if already configured for this specific name
    # We check handlers to prevent duplicates if setup_logger is called multiple times
    if logger.handlers:
        _loggers[name] = logger
        return logger

    # Formatter with ISO8601-like timestamp for reproducibility
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler setup
    if log_file:
        # Use provided path
        log_path = Path(log_file)
    elif log_dir:
        log_path = Path(log_dir) / f"{name}.log"
    else:
        # Default to project_root/logs/
        project_root = _get_project_root()
        log_dir_path = project_root / "logs"
        log_dir_path.mkdir(parents=True, exist_ok=True)
        log_path = log_dir_path / f"{name}.log"

    # Ensure parent directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    fh = logging.FileHandler(str(log_path))
    fh.setLevel(level)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    _loggers[name] = logger
    return logger

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Returns a logger instance, creating it with default settings if necessary.

    Args:
        name: Name of the logger.

    Returns:
        logging.Logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    # Try to load config for default settings if available
    if load_config and get_config_value:
        try:
            config = load_config()
            # Check for logging config in YAML
            if isinstance(config, dict) and 'logging' in config:
                log_cfg = config['logging']
                level_str = log_cfg.get('level', 'INFO').upper()
                level = getattr(logging, level_str, logging.INFO)
                log_dir = log_cfg.get('dir', None)
            else:
                level = logging.INFO
                log_dir = None
        except Exception:
            level = logging.INFO
            log_dir = None
    else:
        level = logging.INFO
        log_dir = None

    return setup_logger(name, level=level, log_dir=log_dir)

# Convenience wrapper functions for common log levels
# These accept a logger instance or name, but standard usage is logger.info(msg)
# The existing API surface shows functions like `info(logger, msg)`.
# We preserve that signature for compatibility with existing imports.

def info(logger, msg: str):
    """Log an info message."""
    if isinstance(logger, str):
        logger = get_logger(logger)
    logger.info(msg)

def debug(logger, msg: str):
    """Log a debug message."""
    if isinstance(logger, str):
        logger = get_logger(logger)
    logger.debug(msg)

def warning(logger, msg: str):
    """Log a warning message."""
    if isinstance(logger, str):
        logger = get_logger(logger)
    logger.warning(msg)

def error(logger, msg: str, exc_info: bool = False):
    """Log an error message."""
    if isinstance(logger, str):
        logger = get_logger(logger)
    logger.error(msg, exc_info=exc_info)

def critical(logger, msg: str):
    """Log a critical message."""
    if isinstance(logger, str):
        logger = get_logger(logger)
    logger.critical(msg)

def setup_audit_logger(
    name: str = "audit",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Sets up a dedicated logger for audit trails.
    Ensures all messages are logged to a file for reproducibility.

    Args:
        name: Logger name.
        log_file: Optional specific file path. Defaults to logs/audit.log.

    Returns:
        Configured audit logger.
    """
    project_root = _get_project_root()
    if not log_file:
        log_dir = project_root / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = str(log_dir / "audit.log")

    logger = setup_logger(name, log_file=log_file, level=logging.INFO)
    # Ensure audit logger only logs to file (or both, but file is mandatory)
    # We keep console for immediate feedback but file is the record.
    return logger