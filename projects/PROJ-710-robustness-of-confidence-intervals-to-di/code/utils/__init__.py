"""
Utilities package for the llmXive automated science pipeline.

This package contains helper functions for project setup, state management,
and common utilities used across the simulation pipeline.
"""
from .init_dirs import create_directories, verify_directories, main as init_dirs_main
from .update_state import (
    compute_file_hash,
    get_git_commit_hash,
    scan_artifacts,
    update_state_manifest,
    verify_state_integrity,
    main as update_state_main
)

__all__ = [
    "create_directories",
    "verify_directories",
    "init_dirs_main",
    "compute_file_hash",
    "get_git_commit_hash",
    "scan_artifacts",
    "update_state_manifest",
    "verify_state_integrity",
    "update_state_main"
]