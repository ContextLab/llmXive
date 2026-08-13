"""
File-based locking utilities for the llmXive pipeline.

This module provides a centralized file lock to ensure serialized access
to shared resources in the data/interim directory, preventing race conditions
during parallel or concurrent pipeline execution.
"""

import os
from pathlib import Path
from filelock import FileLock

# Ensure the lock directory exists before creating the lock instance
LOCK_DIR = Path("data/interim")
LOCK_DIR.mkdir(parents=True, exist_ok=True)

# Define the lock file path
LOCK_FILE_PATH = LOCK_DIR / "pipeline.lock"

# Create the global pipeline lock instance
# This lock will block other processes attempting to acquire it until released
pipeline_lock = FileLock(str(LOCK_FILE_PATH))

def get_lock_path() -> str:
    """
    Returns the absolute path to the pipeline lock file.

    Returns:
        str: The file path to the lock file.
    """
    return str(LOCK_FILE_PATH)

def ensure_lock_directory() -> None:
    """
    Ensures the directory containing the lock file exists.
    This is a safety check in case the directory was removed externally.
    """
    LOCK_DIR.mkdir(parents=True, exist_ok=True)

# For backward compatibility or explicit usage patterns, we expose the lock directly.
# Users should use:
#   from src.utils.locks import pipeline_lock
#   with pipeline_lock:
#       # critical section accessing data/interim
#       ...