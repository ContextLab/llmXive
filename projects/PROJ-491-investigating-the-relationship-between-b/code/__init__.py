"""
llmXive Research Pipeline - Code Package
"""
__version__ = "0.1.0"
__author__ = "llmXive"

# Import key modules for convenience
from .config import ensure_directories
from .state_manager import (
    compute_file_hash,
    compute_directory_hash,
    load_state,
    save_state,
    update_state_artifact,
    update_state_directory,
    verify_artifact_integrity
)

__all__ = [
    'ensure_directories',
    'compute_file_hash',
    'compute_directory_hash',
    'load_state',
    'save_state',
    'update_state_artifact',
    'update_state_directory',
    'verify_artifact_integrity'
]