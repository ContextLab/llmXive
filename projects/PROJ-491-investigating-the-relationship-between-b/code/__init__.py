"""
llmXive research-implementer agent pipeline code package.

This package contains the core implementation for investigating
the relationship between brain network dynamics and anticipatory
reward processing.
"""

import logging
import sys
from pathlib import Path

__version__ = "0.1.0"
__author__ = "llmXive Research Team"

# Configure basic logging infrastructure
# Logs are directed to stderr for immediate visibility during pipeline runs
# and to a file in the data/processed directory for persistence.

LOG_DIR = Path("data/processed")
LOG_FILE = LOG_DIR / "pipeline.log"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Create formatter
_formatter = logging.Formatter(
    fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Create console handler
_console_handler = logging.StreamHandler(sys.stderr)
_console_handler.setFormatter(_formatter)
_console_handler.setLevel(logging.INFO)

# Create file handler
_file_handler = logging.FileHandler(LOG_FILE)
_file_handler.setFormatter(_formatter)
_file_handler.setLevel(logging.DEBUG)

# Configure root logger
_root_logger = logging.getLogger()
_root_logger.setLevel(logging.DEBUG)
_root_logger.addHandler(_console_handler)
_root_logger.addHandler(_file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a named logger for a specific module.

    Args:
        name: The module name (usually __name__).

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)