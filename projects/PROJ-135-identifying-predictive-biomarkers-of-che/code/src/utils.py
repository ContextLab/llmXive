import hashlib
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any

class TimeoutError(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutError("Function call timed out")

def watchdog(func, timeout_seconds: int):
    """
    Executes a function with a timeout.
    """
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    try:
        result = func()
        signal.alarm(0) # Disable alarm
        return result
    except TimeoutError:
        logging.error(f"Watchdog triggered: {func.__name__} exceeded {timeout_seconds}s")
        raise

def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """Sets up logging for a module."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def calculate_checksum(file_path: Path) -> str:
    """Calculates SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def generate_checksums_for_directory(dir_path: Path) -> Dict[str, str]:
    """Generates checksums for all files in a directory."""
    checksums = {}
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            checksums[str(file_path)] = calculate_checksum(file_path)
    return checksums

def ensure_path_exists(path: Path):
    """Ensures a path exists, creating directories if necessary."""
    path.mkdir(parents=True, exist_ok=True)

def get_file_size_mb(file_path: Path) -> float:
    """Returns file size in MB."""
    return file_path.stat().st_size / (1024 * 1024)

def update_state_artifact_hashes(hashes: Dict[str, str]) -> None:
    """
    Updates the state artifact hashes file.
    This is a placeholder implementation; actual logic depends on state management.
    """
    # Assuming state/artifact_hashes.yaml exists or is created
    pass