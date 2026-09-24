import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure the project root is in the path if running as a script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
LOG_DIR = PROJECT_ROOT / "logs"

# Global logger instance
_GLOBAL_LOGGER: Optional[logging.Logger] = None

class ProjectFormatter(logging.Formatter):
    """Custom formatter for structured project logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Standard format with timestamp, level, module, and message
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

def configure_logging_level(level: str = "INFO") -> None:
    """
    Configure the global logging level for the root logger.
    
    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.root.setLevel(numeric_level)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve the global logger, configuring it if it hasn't been set up yet.
    
    This function ensures that the global logger has both FileHandler and 
    ConsoleHandler attached.
    
    Args:
        name: Optional name for the logger. If None, uses 'llmxive'.
    
    Returns:
        A configured logging.Logger instance.
    """
    global _GLOBAL_LOGGER
    
    logger_name = name if name else "llmxive"
    
    if _GLOBAL_LOGGER is None:
        _GLOBAL_LOGGER = logging.getLogger(logger_name)
        _GLOBAL_LOGGER.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers if called multiple times
        if _GLOBAL_LOGGER.hasHandlers():
            _GLOBAL_LOGGER.handlers.clear()
        
        # Ensure log directory exists
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create file handler
        log_file_path = LOG_DIR / "pipeline.log"
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(ProjectFormatter())
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ProjectFormatter())
        
        # Add handlers to the logger
        _GLOBAL_LOGGER.addHandler(file_handler)
        _GLOBAL_LOGGER.addHandler(console_handler)
        
        # Set propagation to False to avoid duplicate logs in parent loggers
        _GLOBAL_LOGGER.propagate = False
    
    return _GLOBAL_LOGGER

def get_module_logger(module_name: str) -> logging.Logger:
    """
    Get a child logger for a specific module.
    
    Args:
        module_name: The name of the module (e.g., 'src.data.preprocess').
    
    Returns:
        A child logger configured with the same handlers as the global logger.
    """
    parent_logger = get_logger()
    child_logger = parent_logger.getChild(module_name)
    return child_logger