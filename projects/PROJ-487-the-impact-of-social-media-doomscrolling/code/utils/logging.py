"""
Logging infrastructure for the llmXive research pipeline.

Provides a centralized logging configuration that writes to both
console (stdout) and a rotating file log.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

# Default log level for the application
DEFAULT_LEVEL = logging.INFO

# Log directory relative to project root
LOG_DIR_NAME = "data/logs"
LOG_FILE_NAME = "pipeline.log"

# Formatter string for log messages
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _ensure_log_dir(project_root: Optional[Path] = None) -> Path:
    """Ensure the log directory exists.
    
    Args:
        project_root: Optional Path to project root. If None, uses current working directory.
        
    Returns:
        Path to the log directory.
    """
    if project_root is None:
        project_root = Path.cwd()
    
    log_dir = project_root / LOG_DIR_NAME
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_logger(
    name: str,
    level: int = DEFAULT_LEVEL,
    project_root: Optional[Path] = None,
    file_mode: bool = True,
    console_mode: bool = True
) -> logging.Logger:
    """Get or create a configured logger instance.
    
    This function ensures a consistent logging configuration across the project.
    It creates a logger with:
    - A RotatingFileHandler (if file_mode is True)
    - A StreamHandler for stdout (if console_mode is True)
    - A consistent format string and date format
    
    Args:
        name: Name of the logger (usually __name__ of the module).
        level: Logging level (e.g., logging.INFO).
        project_root: Optional Path to project root. Defaults to current working directory.
        file_mode: If True, log to a file in data/logs/.
        console_mode: If True, log to stdout.
        
    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        logger.setLevel(level)
        return logger
    
    logger.setLevel(level)
    logger.propagate = False  # Prevent duplicate logs from parent loggers
    
    # Create formatters
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    log_dir = _ensure_log_dir(project_root)
    log_file_path = log_dir / LOG_FILE_NAME
    
    # File handler (rotating)
    if file_mode:
        # 5MB max size, keep 5 backup files
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Console handler
    if console_mode:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def configure_root_logger(
    level: int = DEFAULT_LEVEL,
    project_root: Optional[Path] = None
) -> None:
    """Configure the root logger for the entire application.
    
    This should be called once at the entry point of the application
    to set up the global logging behavior.
    
    Args:
        level: Logging level for the root logger.
        project_root: Optional Path to project root.
    """
    logger = get_logger(
        name="root",
        level=level,
        project_root=project_root,
        file_mode=True,
        console_mode=True
    )
    # Ensure the root logger doesn't propagate to system loggers
    logger.propagate = False


# Convenience function for quick logging setup in scripts
def setup_logging(
    level: int = DEFAULT_LEVEL,
    project_root: Optional[Path] = None
) -> logging.Logger:
    """Convenience function to set up logging and return the root logger.
    
    Args:
        level: Logging level.
        project_root: Optional Path to project root.
        
    Returns:
        The configured root logger.
    """
    configure_root_logger(level, project_root)
    return logging.getLogger("root")