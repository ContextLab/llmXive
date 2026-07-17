"""
Logging utility module for the molecular surface area prediction project.
Provides centralized logging configuration and logger retrieval.
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from .config import get_project_root, load_env_config

# Global logging configuration flag
_logging_configured = False

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    project_root: Optional[Path] = None
) -> None:
    """
    Configure the root logger for the project.
    
    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG)
        log_file: Optional path to log file. If None, logs to console only.
        project_root: Optional project root path. If None, uses get_project_root().
    """
    global _logging_configured
    
    if _logging_configured:
        return
    
    root_path = project_root or get_project_root()
    log_dir = root_path / "results" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_path = log_dir / log_file
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    
    _logging_configured = True

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    # Ensure logging is configured
    setup_logging()
    
    logger = logging.getLogger(name)
    return logger

def get_logger_level(logger_name: str) -> int:
    """
    Get the current logging level for a specific logger.
    
    Args:
        logger_name: Name of the logger
    
    Returns:
        Current logging level
    """
    logger = logging.getLogger(logger_name)
    return logger.level
