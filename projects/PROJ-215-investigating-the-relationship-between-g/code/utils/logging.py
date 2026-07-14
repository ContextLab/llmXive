import logging
import os
from pathlib import Path
from typing import Optional

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    project_root: Optional[str] = None
) -> None:
    """
    Configure logging for the project.
    
    Args:
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO)
        log_file: Optional path to a log file. If None, logs to console only.
        project_root: Optional root directory for the project. Used to resolve log_file path.
    """
    if project_root:
        log_dir = Path(project_root) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        if log_file:
            log_file = str(log_dir / log_file)
        else:
            log_file = str(log_dir / "pipeline.log")

    handlers = []
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    handlers.append(console_handler)

    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            handlers.append(file_handler)
        except (OSError, PermissionError) as e:
            print(f"Warning: Could not create log file {log_file}: {e}")

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    for handler in handlers:
        root_logger.addHandler(handler)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Name of the logger. If None, returns the root logger.
    
    Returns:
        A configured logger instance.
    """
    if name:
        return logging.getLogger(name)
    return logging.getLogger()
