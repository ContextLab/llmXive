import logging
import sys
import os
from pathlib import Path
from typing import Optional, Union, Dict, Any

class ProjectError(Exception):
    """Base exception for project errors."""
    pass

class DataNotFoundError(ProjectError):
    """Raised when required data is not found."""
    pass

class ConfigurationError(ProjectError):
    """Raised when configuration is invalid."""
    pass

class APIError(ProjectError):
    """Raised when an API call fails."""
    pass

def get_project_root() -> Path:
    """Return the project root directory."""
    # Assuming code/ is in the root
    return Path(__file__).resolve().parent.parent

def get_data_dir() -> Path:
    """Return the data directory."""
    return get_project_root() / "data"

def get_code_dir() -> Path:
    """Return the code directory."""
    return get_project_root() / "code"

def get_tests_dir() -> Path:
    """Return the tests directory."""
    return get_project_root() / "tests"

def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure a directory exists."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def setup_logging(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Setup logging for a module.
    
    Args:
        name: Module name (e.g., __name__)
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Default level
    if level is None:
        level = logging.INFO
    
    # Prevent adding multiple handlers if called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    # Set level - ensure it's an integer or valid string
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    logger.setLevel(level)
    return logger
