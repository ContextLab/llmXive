import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from .config import get_config

# Global logger registry to ensure single instance per module
_loggers: dict[str, logging.Logger] = {}

def get_log_file_path(log_filename: str = "project.log") -> Path:
    """
    Determine the absolute path for the log file.
    Uses the configured data directory from config.py.
    Falls back to 'data/logs' if config is not yet initialized.
    """
    config = get_config()
    if config and hasattr(config, 'paths'):
        log_dir = config.paths.data_dir / "logs"
    else:
        # Fallback relative to project root (assumed current working directory)
        log_dir = Path("data") / "logs"

    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / log_filename

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_str: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 3
) -> None:
    """
    Configure the root logger and project-specific handlers.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional filename for the log file. Defaults to 'project.log'.
        format_str: Optional custom format string. Defaults to standard format.
        enable_console: Whether to add a StreamHandler to stdout.
        enable_file: Whether to add a RotatingFileHandler.
        max_bytes: Max size per log file before rotation.
        backup_count: Number of backup files to keep.
    """
    if format_str is None:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(format_str)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates on re-calls (e.g. in tests)
    root_logger.handlers.clear()

    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    if enable_file:
        file_path = get_log_file_path(log_file)
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve or create a named logger.
    This ensures consistent configuration across the application.
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    # If setup_logging hasn't been called yet, the root logger might not have handlers.
    # We rely on the root logger's propagation to handle this, or call setup_logging explicitly.
    _loggers[name] = logger
    return logger

def init_logger(
    module_name: str,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Convenience function to setup logging and get a logger for a specific module.
    This is the recommended entry point for scripts.
    """
    setup_logging(level=level)
    return get_logger(module_name)
