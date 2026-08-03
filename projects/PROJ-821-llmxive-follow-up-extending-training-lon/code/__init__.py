"""
llmXive code package initialization.

This package contains the core implementation for the automated science pipeline,
including data generation, inference, and analysis modules.
"""

import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Ensure the package is recognized and ready for imports
__version__ = "0.1.0"
__author__ = "llmXive Research Team"

# Initialize sub-packages if needed
try:
    from . import config
except ImportError:
    pass

try:
    from . import data_generation
except ImportError:
    pass

try:
    from . import inference
except ImportError:
    pass

try:
    from . import analysis
except ImportError:
    pass

# --- Base Logging Infrastructure ---

def get_project_root() -> Path:
    """
    Returns the root directory of the llmXive project.
    Assumes the project root is the parent of the 'code' directory.
    """
    return Path(__file__).resolve().parent.parent

def get_log_path() -> Path:
    """
    Returns the path to the logs directory within data/results/logs.
    Creates the directory if it does not exist.
    """
    root = get_project_root()
    log_dir = root / "data" / "results" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configures and returns a logger with console and optional file handlers.

    Args:
        name: The name of the logger (usually __name__).
        log_file: Optional relative filename for the log file (e.g., "pipeline.log").
                  If None, only console output is used.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers multiple times if this function is called repeatedly
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (if requested)
    if log_file:
        log_dir = get_log_path()
        file_path = log_dir / log_file
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# Convenience function to get a standard logger for the code package
def get_default_logger() -> logging.Logger:
    """
    Returns a default logger configured for the llmXive code package.
    Logs to 'pipeline.log' in the data/results/logs directory.
    """
    return setup_logger("llmXive", "pipeline.log")
