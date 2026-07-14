"""
Code package initialization.

Exposes key functions and ensures logging is configured.
"""

from code.config import CONFIG, get_project_root, ensure_dirs
from code.logging_utils import get_logger, setup_file_logging, warn_missing_metadata

# Initialize directories on import
ensure_dirs()

__all__ = [
    'CONFIG',
    'get_project_root',
    'ensure_dirs',
    'get_logger',
    'setup_file_logging',
    'warn_missing_metadata',
]