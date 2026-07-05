"""
Utility functions for logging, error handling, and checksum validation.
"""
import hashlib
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Configure default logging format
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name: str,
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    console: bool = True
) -> logging.Logger:
    """
    Setup and return a logger with optional file and console handlers.

    Args:
        name: Logger name (typically __name__ of the calling module).
        log_file: Optional path to write log output.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        console: Whether to log to stderr.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT)

    if console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if log_file:
        # Ensure directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def validate_checksum(file_path: Path, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """
    Calculate and validate the checksum of a file.

    Args:
        file_path: Path to the file to check.
        expected_checksum: Expected hexadecimal checksum string.
        algorithm: Hash algorithm to use (default: 'sha256').

    Returns:
        True if checksums match, False otherwise.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is unsupported or checksum format is invalid.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for checksum validation: {file_path}")

    if algorithm not in hashlib.algorithms_available:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    hasher = hashlib.new(algorithm)

    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files (e.g., VCFs)
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
    except IOError as e:
        raise IOError(f"Failed to read file for checksum calculation: {file_path}") from e

    calculated_checksum = hasher.hexdigest()

    # Normalize case for comparison
    if calculated_checksum.lower() == expected_checksum.lower():
        return True
    else:
        logging.getLogger(__name__).warning(
            f"Checksum mismatch for {file_path}. "
            f"Expected: {expected_checksum}, Got: {calculated_checksum}"
        )
        return False


def calculate_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate the checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use.

    Returns:
        Hexadecimal checksum string.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if algorithm not in hashlib.algorithms_available:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    hasher = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def handle_critical_error(message: str, error_code: int = 1) -> None:
    """
    Log a critical error and exit the program.

    Args:
        message: Error message to log.
        error_code: Exit code to use.
    """
    logger = logging.getLogger(__name__)
    logger.critical(f"FATAL ERROR: {message}")
    sys.exit(error_code)


def log_pipeline_start(task_id: str, config: Optional[Dict[str, Any]] = None) -> None:
    """
    Log the start of a pipeline task.

    Args:
        task_id: Identifier for the task (e.g., 'T005').
        config: Optional configuration dictionary to log.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Starting task: {task_id}")
    if config:
        logger.debug(f"Configuration: {config}")


def log_pipeline_end(task_id: str, success: bool = True, duration_seconds: Optional[float] = None) -> None:
    """
    Log the end of a pipeline task.

    Args:
        task_id: Identifier for the task.
        success: Whether the task completed successfully.
        duration_seconds: Optional execution duration.
    """
    logger = logging.getLogger(__name__)
    status = "SUCCESS" if success else "FAILED"
    msg = f"Task {task_id} completed with status: {status}"
    if duration_seconds is not None:
        msg += f" (Duration: {duration_seconds:.2f}s)"
    
    if success:
        logger.info(msg)
    else:
        logger.error(msg)
