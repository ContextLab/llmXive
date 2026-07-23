import hashlib
import json
import logging
import os
import signal
import sys
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import psutil

from src.config import PROJECT_ROOT, ensure_directories

# Custom exception for timeout
class TimeoutError(Exception):
    """Custom timeout exception for the watchdog mechanism."""
    pass

# --- Logging Setup ---

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Sets up the logging configuration for the project.

    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to a log file. If None, logs only to console.

    Returns:
        The configured root logger.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File Handler (if specified)
    if log_file:
        # Ensure directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(console_format)
        logger.addHandler(file_handler)

    return logger

# --- Checksum Generation ---

def calculate_checksum(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Calculates the checksum of a file using the specified algorithm.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string of the checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()

def generate_checksums_for_directory(
    directory: Union[str, Path], 
    output_file: Union[str, Path], 
    algorithm: str = 'sha256',
    extensions: Optional[List[str]] = None
) -> Dict[str, str]:
    """
    Recursively generates checksums for all files in a directory and saves them to a JSON file.

    Args:
        directory: Path to the directory to scan.
        output_file: Path to the output JSON file.
        algorithm: Hash algorithm to use.
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.json']). 
                    If None, all files are included.

    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    directory = Path(directory)
    output_file = Path(output_file)
    
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    checksums: Dict[str, str] = {}
    logger = logging.getLogger(__name__)

    for file_path in directory.rglob('*'):
        if file_path.is_file():
            # Filter by extension if provided
            if extensions is not None:
                if file_path.suffix not in extensions:
                    continue
            
            try:
                checksum = calculate_checksum(file_path, algorithm)
                # Store relative path from the directory root
                relative_path = str(file_path.relative_to(directory))
                checksums[relative_path] = checksum
                logger.debug(f"Checksum calculated for {relative_path}: {checksum[:16]}...")
            except Exception as e:
                logger.error(f"Failed to calculate checksum for {file_path}: {e}")

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2)

    logger.info(f"Checksums saved to {output_file}")
    return checksums

# --- Timeout Watchdog ---

def timeout_handler(signum: int, frame: Any) -> None:
    """
    Signal handler for timeout. Raises TimeoutError.
    """
    raise TimeoutError("Execution exceeded the maximum allowed time limit.")

def watchdog(func: Callable, timeout_seconds: int = 18000) -> Callable:
    """
    Decorator to enforce a timeout on a function execution.
    Default timeout is 5 hours (18000 seconds).

    Args:
        func: The function to wrap.
        timeout_seconds: Maximum allowed execution time in seconds.

    Returns:
        The wrapped function.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Set the signal handler
        original_handler = signal.signal(signal.SIGALRM, timeout_handler)
        
        try:
            # Set the alarm
            signal.alarm(timeout_seconds)
            result = func(*args, **kwargs)
            return result
        except TimeoutError:
            logging.getLogger(__name__).critical(
                f"Function {func.__name__} timed out after {timeout_seconds} seconds."
            )
            raise
        finally:
            # Cancel the alarm and restore the original handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, original_handler)
    
    return wrapper

# --- Helper Functions ---

def ensure_path_exists(path: Union[str, Path]) -> Path:
    """
    Ensures that a path exists, creating directories if necessary.

    Args:
        path: The path to ensure exists.

    Returns:
        The Path object.
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """
    Gets the size of a file in megabytes.

    Args:
        file_path: Path to the file.

    Returns:
        File size in MB.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return 0.0
    return file_path.stat().st_size / (1024 * 1024)

def update_state_artifact_hashes(hashes: Dict[str, str]) -> None:
    """
    Updates the state/artifact_hashes.yaml file with new checksums.
    
    Args:
        hashes: Dictionary of relative paths to checksums.
    """
    import yaml
    
    state_file = PROJECT_ROOT / "state" / "artifact_hashes.yaml"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    current_hashes = {}
    if state_file.exists():
        with open(state_file, 'r') as f:
            current_hashes = yaml.safe_load(f) or {}
    
    current_hashes.update(hashes)
    
    with open(state_file, 'w') as f:
        yaml.dump(current_hashes, f, default_flow_style=False)
    
    logging.info(f"Updated state artifact hashes at {state_file}")
