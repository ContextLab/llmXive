"""
Logging Configuration Module.

Provides centralized logging setup for the Solder Hardness project.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional
from utils.error_handlers import ConfigurationError

# Default log level
DEFAULT_LOG_LEVEL = logging.INFO

# Default log format
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Log file path
LOG_FILE_PATH = None

def setup_logging(
    level: Optional[int] = None,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
    project_root: Optional[Path] = None
) -> None:
    """
    Configure the root logger for the project.
    
    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_format: Format string for log messages.
        log_file: Path to log file (optional).
        project_root: Project root directory (optional).
    """
    # Get configuration from environment or defaults
    log_level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, DEFAULT_LOG_LEVEL) if level is None else level
    
    log_fmt = log_format if log_format else DEFAULT_LOG_FORMAT
    
    # Get log file path
    log_file_path = log_file
    if log_file_path is None:
        log_file_env = os.environ.get('LOG_FILE')
        if log_file_env:
            log_file_path = log_file_env
        elif project_root:
            log_file_path = project_root / "logs" / "pipeline.log"
        else:
            log_file_path = Path("logs") / "pipeline.log"
    
    # Create log directory if needed
    log_file_path = Path(log_file_path)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(log_fmt)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Create file handler if log file is specified
    if log_file_path:
        try:
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(log_level)
            file_handler.setFormatter(console_formatter)
            root_logger.addHandler(file_handler)
            logging.info(f"Logging to file: {log_file_path}")
        except Exception as e:
            logging.warning(f"Failed to create file handler: {str(e)}. Logging to console only.")

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (defaults to module name if None).
        
    Returns:
        A configured logger instance.
    """
    if name is None:
        # Get module name
        import inspect
        frame = inspect.currentframe()
        try:
            frame = frame.f_back
            module = inspect.getmodule(frame)
            name = module.__name__ if module else 'root'
        finally:
            del frame
    
    logger = logging.getLogger(name)
    return logger

def init_project_logger(project_root: Optional[Path] = None) -> logging.Logger:
    """
    Initialize the project logging infrastructure.
    
    Args:
        project_root: Project root directory (optional).
        
    Returns:
        The root logger instance.
    """
    setup_logging(project_root=project_root)
    return get_logger()
