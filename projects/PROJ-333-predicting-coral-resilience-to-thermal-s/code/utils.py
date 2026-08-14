import hashlib
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Sets up a logger (duplicate of utils.logging for convenience in some contexts, but using the main module)."""
    # Prefer the dedicated module if available, otherwise define here
    try:
        from utils.logging import setup_logger as core_setup_logger
        return core_setup_logger(name, log_file, level)
    except ImportError:
        logger = logging.getLogger(name)
        logger.setLevel(level)
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(ch)
        return logger

def validate_checksum(file_path: Path, expected: str, algorithm: str = 'sha256') -> bool:
    """Validates a file's checksum."""
    h = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest().lower() == expected.lower()

def calculate_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """Calculates the checksum of a file."""
    h = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def handle_critical_error(logger: logging.Logger, message: str, error: Exception) -> None:
    """Logs a critical error and exits."""
    logger.critical(f"{message}: {error}")
    sys.exit(1)

def log_pipeline_start(logger: logging.Logger, task_id: str) -> None:
    """Logs the start of a pipeline task."""
    logger.info(f"Pipeline Task {task_id} started at {time.strftime('%Y-%m-%d %H:%M:%S')}")

def log_pipeline_end(logger: logging.Logger, task_id: str, status: str) -> None:
    """Logs the end of a pipeline task."""
    logger.info(f"Pipeline Task {task_id} finished with status: {status}")
