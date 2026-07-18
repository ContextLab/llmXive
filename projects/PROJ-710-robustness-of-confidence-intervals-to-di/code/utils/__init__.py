"""
Utility functions and helpers for the robustness of confidence intervals to DP noise project.

This package provides:
- State management and artifact hashing (update_state)
- Logging configuration and integration
- Validation utilities for data and configuration
"""

from .update_state import (
    compute_file_hash,
    get_git_commit_hash,
    scan_artifacts,
    update_state_manifest,
    verify_state_integrity,
    main as update_state_main
)

__all__ = [
    'compute_file_hash',
    'get_git_commit_hash',
    'scan_artifacts',
    'update_state_manifest',
    'verify_state_integrity',
    'update_state_main'
]

__version__ = "0.1.0"