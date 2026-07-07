"""
Logging configuration for the llmXive research pipeline.

Provides a centralized logging setup to ensure consistent formatting
and output destinations across all pipeline modules.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

# Global logger instance cache
_loggers: dict = {}

def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    project_root: Optional[str] = None
) -> logging.Logger:
    """
    Configure the root logger and return a project-specific logger.
    
    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to a log file. If None, logs only to console.
        project_root: Optional path to the project root for relative log file paths.
        
    Returns:
        The configured root logger.
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    if root_logger.handlers:
        root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        if project_root:
            log_path = Path(project_root) / log_file
        
        # Ensure log directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(log_level)
        file_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)

    return root_logger

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get or create a named logger.
    
    Args:
        name: The name of the logger (usually __name__ of the module).
        
    Returns:
        A configured logger instance.
    """
    if name not in _loggers:
        logger = logging.getLogger(name)
        if not logger.handlers:
            # Inherit handlers from root if not explicitly configured
            root_logger = logging.getLogger()
            if not root_logger.handlers:
                # Fallback to default setup if root isn't configured yet
                setup_logging()
        _loggers[name] = logger
    return _loggers[name]