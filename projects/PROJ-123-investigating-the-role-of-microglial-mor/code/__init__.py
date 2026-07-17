"""
Code package initialization.

Exposes key functions and ensures logging is configured.
Handles warnings for missing metadata (FR-001, FR-008).
"""

import logging
import sys
from pathlib import Path

from code.config import CONFIG, get_project_root, ensure_dirs
from code.logging_utils import get_logger, setup_file_logging, warn_missing_metadata

# Initialize directories on import
ensure_dirs()

# Configure root logger for the project
# Use a file handler to persist logs and a stream handler for console output
def _configure_root_logger():
    log_dir = get_project_root() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "pipeline.log"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers to avoid duplicates on re-import
    root_logger.handlers.clear()

    # File handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    root_logger.addHandler(fh)

    # Stream handler
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.WARNING)
    sh.setFormatter(formatter)
    root_logger.addHandler(sh)

    # Specific warning handler for missing metadata (FR-001, FR-008)
    # Logs warnings to both file and console with a specific tag
    missing_meta_logger = logging.getLogger("code.metadata_warnings")
    missing_meta_logger.setLevel(logging.WARNING)
    missing_meta_logger.propagate = False  # Prevent double logging if root handles it

    # Add specific handler for metadata warnings
    meta_handler = logging.FileHandler(log_dir / "metadata_warnings.log")
    meta_handler.setLevel(logging.WARNING)
    meta_formatter = logging.Formatter(
        '%(asctime)s - METADATA_WARNING - %(message)s'
    )
    meta_handler.setFormatter(meta_formatter)
    missing_meta_logger.addHandler(meta_handler)

    # Also log to console for immediate visibility
    meta_console = logging.StreamHandler(sys.stdout)
    meta_console.setLevel(logging.WARNING)
    meta_console.setFormatter(meta_formatter)
    missing_meta_logger.addHandler(meta_console)

    return missing_meta_logger

# Initialize the metadata warning logger immediately
_meta_warning_logger = _configure_root_logger()

# Override warn_missing_metadata to use our specific logger if needed,
# or ensure the global setup handles it. The function in logging_utils
# is designed to be called explicitly where metadata is checked.
# We ensure the infrastructure is ready for it.

__all__ = [
    'CONFIG',
    'get_project_root',
    'ensure_dirs',
    'get_logger',
    'setup_file_logging',
    'warn_missing_metadata',
    '_meta_warning_logger',
]