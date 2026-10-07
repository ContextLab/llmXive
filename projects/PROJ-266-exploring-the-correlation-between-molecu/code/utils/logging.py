import logging
import sys
from pathlib import Path
from typing import Optional
from .config import get_project_root

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    """
    return logging.getLogger(name)

def configure_root_logger(level: int = logging.INFO) -> None:
    """
    Configure the root logger for the application.
    """
    if not logging.getLogger().handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(level)

def get_log_path() -> Path:
    """
    Get the path where logs should be written.
    """
    return get_project_root() / "logs"

def setup_logging_for_script(script_name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger specifically for a script, optionally writing to a file.
    """
    logger = logging.getLogger(script_name)
    logger.setLevel(level)
    
    # Ensure root logger is configured
    configure_root_logger(level)
    
    return logger
