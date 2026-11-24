"""
Logging configuration for the Code Maintainability project.
Provides a consistent interface for logger instantiation and 
project-wide logging setup, integrating with the llmxive_toolkit.
"""
import logging
from pathlib import Path
from llmxive_toolkit import get_logger as toolkit_get_logger

def setup_project_logging(name: str, log_file: str) -> logging.Logger:
    """
    Configure logging for a specific project module.
    Ensures the log directory exists and returns a logger that writes to the specified file.
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Use the toolkit's get_logger which handles the boilerplate
    return toolkit_get_logger(name, log_file=log_file)

def setup_logging(name: str) -> logging.Logger:
    """
    Convenience wrapper for setup_project_logging with a default path.
    """
    log_file = f"data/logs/{name}.log"
    return setup_project_logging(name, log_file)

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a logger instance via the toolkit.
    """
    return toolkit_get_logger(name)
