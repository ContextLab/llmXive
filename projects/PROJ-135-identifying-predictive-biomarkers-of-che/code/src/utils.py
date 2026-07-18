"""
Utility functions for the Chemo Biomarker Discovery project.

Provides logging setup, checksum generation, and timeout watchdog.
"""

import hashlib
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional

class TimeoutError(Exception):
    """Custom timeout error."""
    pass

def setup_logging(name: str = "project", level: int = logging.INFO) -> logging.Logger:
    """
    Setup logging configuration.

    Args:
        name: Logger name.
        level: Logging level.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

def calculate_checksum(file_path: Path) -> str:
    """
    Calculate SHA256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hex digest of the checksum.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_checksums_for_directory(dir_path: Path) -> dict:
    """
    Generate checksums for all files in a directory.

    Args:
        dir_path: Path to the directory.

    Returns:
        Dictionary mapping filenames to checksums.
    """
    checksums = {}
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
          checksums[str(file_path.relative_to(dir_path))] = calculate_checksum(file_path)
    return checksums

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Operation timed out")

def watchdog(timeout_seconds: int):
    """
    Set up a watchdog timer.

    Args:
        timeout_seconds: Timeout duration in seconds.
    """
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)

def ensure_path_exists(path: Path):
    """Ensure a path exists, creating directories if necessary."""
    path.mkdir(parents=True, exist_ok=True)

def get_file_size_mb(file_path: Path) -> float:
    """Get file size in megabytes."""
    return file_path.stat().st_size / (1024 * 1024)

def update_state_artifact_hashes(file_path: Path, state_file: Path) -> None:
    """
    Update the state file with the checksum of the downloaded artifact.

    Args:
        file_path: Path to the downloaded file.
        state_file: Path to the state/artifact_hashes.yaml file.
    """
    import yaml
    checksum = calculate_checksum(file_path)
    state_file.parent.mkdir(parents=True, exist_ok=True)

    state_data = {}
    if state_file.exists():
        with open(state_file, 'r') as f:
            state_data = yaml.safe_load(f) or {}

    state_data[file_path.name] = {
        "checksum": checksum,
        "path": str(file_path),
        "size_bytes": file_path.stat().st_size
    }

    with open(state_file, 'w') as f:
        yaml.dump(state_data, f)
