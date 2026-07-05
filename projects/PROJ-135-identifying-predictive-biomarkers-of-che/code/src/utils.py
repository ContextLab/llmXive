"""
Utility functions for the llmXive chemo-biomarker pipeline.

Provides:
- Logging setup (file + console, with rotation)
- Checksum generation for data integrity
- Timeout watchdog mechanism
"""
import hashlib
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional, Dict

# Project config import (assumed to be available per T004)
# If config.py is in code/src, we import relative to that structure.
try:
    from config import LOG_DIR, DATA_DIR, RESULTS_DIR, MAX_RUNTIME_SECONDS
except ImportError:
    # Fallback if running from root or different context
    # This should ideally be resolved by the project structure setup in T001/T004
    LOG_DIR = Path("results/logs")
    DATA_DIR = Path("data")
    RESULTS_DIR = Path("results")
    MAX_RUNTIME_SECONDS = 5 * 3600  # 5 hours default fallback

# Ensure directories exist
LOG_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def setup_logging(
    name: str = "pipeline",
    log_file: Optional[Path] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Configure logging for the pipeline.
    
    Args:
        name: Logger name.
        log_file: Optional path to log file. If None, uses default timestamped file.
        level: Logging level.
        
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = LOG_DIR / f"{name}_{timestamp}.log"
    else:
        log_file = Path(log_file)
        
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)
    
    return logger


def calculate_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate the checksum of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default sha256).
        
    Returns:
        Hex digest string of the file hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)
            
    return hash_func.hexdigest()


def generate_checksums_for_directory(
    directory: Path,
    output_file: Path,
    recursive: bool = True,
    extensions: Optional[list] = None
) -> Dict[str, str]:
    """
    Generate checksums for all files in a directory and save to JSON.
    
    Args:
        directory: Root directory to scan.
        output_file: Path to the output JSON file.
        recursive: Whether to scan subdirectories.
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.parquet']).
        
    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    directory = Path(directory)
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
        
    checksums = {}
    
    if recursive:
        files = directory.rglob("*")
    else:
        files = directory.iterdir()
        
    for file_path in files:
        if file_path.is_file():
            if extensions:
                if file_path.suffix.lower() not in [ext.lower() for ext in extensions]:
                    continue
            
            try:
                rel_path = file_path.relative_to(directory)
                checksum = calculate_checksum(file_path)
                checksums[str(rel_path)] = checksum
            except Exception as e:
                # Log but continue on individual file errors
                logging.getLogger(__name__).warning(f"Failed to checksum {file_path}: {e}")
    
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w") as f:
        json.dump(checksums, f, indent=2)
        
    return checksums


class TimeoutError(Exception):
    """Custom exception for timeout watchdog."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError(f"Process exceeded the maximum runtime of {MAX_RUNTIME_SECONDS} seconds.")


def watchdog(
    func: Callable,
    timeout_seconds: Optional[int] = None,
    *args,
    **kwargs
) -> Any:
    """
    Execute a function with a timeout watchdog.
    
    Note: This uses signal.SIGALRM which only works on Unix-like systems.
    For Windows or cross-platform support, a threading-based approach would be needed.
    
    Args:
        func: The function to execute.
        timeout_seconds: Timeout in seconds. Defaults to MAX_RUNTIME_SECONDS from config.
        *args: Arguments to pass to func.
        **kwargs: Keyword arguments to pass to func.
        
    Returns:
        The result of func(*args, **kwargs).
        
    Raises:
        TimeoutError: If the function execution exceeds the timeout.
    """
    if timeout_seconds is None:
        timeout_seconds = MAX_RUNTIME_SECONDS
        
    # Set the signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    
    try:
        # Set the alarm
        signal.alarm(timeout_seconds)
        
        # Execute the function
        result = func(*args, **kwargs)
        
        # Cancel the alarm
        signal.alarm(0)
        
        return result
        
    except TimeoutError as e:
        logging.getLogger(__name__).critical(f"Timeout triggered: {e}")
        # Write a failure state if needed
        failure_state = {
            "status": "halted",
            "reason": "runtime_timeout",
            "timestamp": datetime.now().isoformat()
        }
        state_file = RESULTS_DIR / "timeout_state.json"
        with open(state_file, "w") as f:
            json.dump(failure_state, f, indent=2)
        raise e
        
    finally:
        # Restore the old handler
        signal.signal(signal.SIGALRM, old_handler)


def ensure_path_exists(path: Path) -> Path:
    """Ensure a path exists, creating directories if necessary."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_file_size_mb(file_path: Path) -> float:
    """Get file size in megabytes."""
    return file_path.stat().st_size / (1024 * 1024)