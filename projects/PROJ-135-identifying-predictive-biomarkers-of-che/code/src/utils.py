import hashlib
import json
import logging
import os
import signal
import sys
import time
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
import psutil
import threading

logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    """Custom timeout exception."""
    pass

def setup_logging(level: int = logging.INFO):
    """Configure logging for the application."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def calculate_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Calculate checksum for a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use
        
    Returns:
        Hexadecimal checksum string
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def generate_checksums_for_directory(dir_path: Path, pattern: str = '*') -> Dict[str, str]:
    """
    Generate checksums for all files in a directory.
    
    Args:
        dir_path: Directory to scan
        pattern: Glob pattern for files
        
    Returns:
        Dict mapping relative file paths to checksums
    """
    checksums = {}
    for file_path in dir_path.glob(pattern):
        if file_path.is_file():
          rel_path = file_path.relative_to(dir_path)
          checksums[str(rel_path)] = calculate_checksum(file_path)
    return checksums

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Operation timed out")

def watchdog(func, timeout_seconds: int, *args, **kwargs):
    """
    Execute function with timeout.
    
    Args:
        func: Function to execute
        timeout_seconds: Maximum execution time
        *args, **kwargs: Arguments to pass to function
        
    Returns:
        Function result
        
    Raises:
        TimeoutError: If function exceeds timeout
    """
    # Set up signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)
    
    try:
        result = func(*args, **kwargs)
        signal.alarm(0)  # Cancel alarm
        return result
    except TimeoutError:
        raise
    finally:
        signal.signal(signal.SIGALRM, old_handler)

def ensure_path_exists(path: Path):
    """Ensure a path exists, creating directories if necessary."""
    path.mkdir(parents=True, exist_ok=True)

def get_file_size_mb(file_path: Path) -> float:
    """Get file size in megabytes."""
    return file_path.stat().st_size / (1024 * 1024)

def update_state_artifact_hashes(state_file: Path, checksums: Dict[str, str]):
    """
    Update the state artifact file with checksums.
    
    Args:
        state_file: Path to the state YAML file
        checksums: Dict of file paths to checksums
    """
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state or create new
    if state_file.exists():
        with open(state_file, 'r') as f:
            state = yaml.safe_load(f) or {}
    else:
        state = {"artifact_hashes": {}}
    
    # Update checksums
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}
    
    state["artifact_hashes"].update(checksums)
    
    # Write back
    with open(state_file, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
    
    logger.info(f"Updated state file with {len(checksums)} checksums: {state_file}")