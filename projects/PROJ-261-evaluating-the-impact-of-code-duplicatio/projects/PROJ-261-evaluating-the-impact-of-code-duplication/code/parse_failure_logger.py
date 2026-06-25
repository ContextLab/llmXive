"""Parse failure logging infrastructure.

This module provides thread-safe logging of parse failures to a CSV file.
It is used by ast_cloner and other modules to record parsing errors for
debugging and analysis.

Per Constitution Principle III (Data Hygiene), all parse failures are
logged with full context for reproducibility.
"""
import csv
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Module-level logger
_logger = None
_logger_lock = threading.Lock()

# Thread-safe file lock for CSV writing
_file_lock = threading.Lock()

def _get_logger() -> logging.Logger:
    """Get or create the module logger."""
    global _logger
    if _logger is None:
        with _logger_lock:
            if _logger is None:
                _logger = logging.getLogger("parse_failure_logger")
                _logger.setLevel(logging.INFO)
                if not _logger.handlers:
                    handler = logging.StreamHandler()
                    handler.setFormatter(logging.Formatter(
                        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    ))
                    _logger.addHandler(handler)
    return _logger

def init_logger(name: str = "parse_failure") -> logging.Logger:
    """Initialize a logger with the given name.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)

    return logger

def log_parse_failure(
    log_path: Path,
    failure_data: Dict,
    append: bool = True
) -> None:
    """Log a parse failure to a CSV file.

    This function is thread-safe and will create the CSV file with headers
    if it doesn't exist.

    Args:
        log_path: Path to the CSV log file
        failure_data: Dictionary containing failure information
        append: If True, append to existing file; if False, overwrite
    """
    logger = _get_logger()

    log_path = Path(log_path)

    # Ensure parent directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Define standard fields for parse failures
    standard_fields = [
        "file_path",
        "clone_density",
        "error_message",
        "timestamp",
        "status",
        "node_count"
    ]

    # Use standard fields or extract from data
    fieldnames = standard_fields
    for key in failure_data.keys():
        if key not in fieldnames:
            fieldnames.append(key)

    with _file_lock:
        file_exists = log_path.exists()

        try:
            with open(log_path, mode="a" if append else "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                # Write header if file is new
                if not file_exists or not append:
                    writer.writeheader()
                    logger.info(f"Created parse failure log: {log_path}")

                # Write failure data
                writer.writerow(failure_data)

            logger.debug(f"Logged parse failure to {log_path}")

        except Exception as e:
            logger.error(f"Failed to write parse failure log: {type(e).__name__}: {e}")
            raise

def log_network_failure(
    log_path: Path,
    endpoint: str,
    error_message: str,
    attempt_number: int,
    timestamp: Optional[str] = None
) -> None:
    """Log a network failure to a CSV file.

    Args:
        log_path: Path to the CSV log file
        endpoint: API endpoint that failed
        error_message: Description of the error
        attempt_number: Which retry attempt failed
        timestamp: Optional ISO timestamp
    """
    if timestamp is None:
        timestamp = datetime.now().isoformat()

    failure_data = {
        "failure_type": "network",
        "endpoint": endpoint,
        "error_message": error_message,
        "attempt_number": attempt_number,
        "timestamp": timestamp
    }

    log_parse_failure(log_path, failure_data)

def log_perplexity_failure(
    log_path: Path,
    sample_id: str,
    error_message: str,
    perplexity_value: Optional[float] = None
) -> None:
    """Log a perplexity computation failure.

    Args:
        log_path: Path to the CSV log file
        sample_id: ID of the code sample
        error_message: Description of the error
        perplexity_value: The perplexity value if available (may be NaN/inf)
    """
    timestamp = datetime.now().isoformat()

    failure_data = {
        "failure_type": "perplexity",
        "sample_id": sample_id,
        "error_message": error_message,
        "perplexity_value": perplexity_value,
        "timestamp": timestamp
    }

    log_parse_failure(log_path, failure_data)

def read_parse_failures(log_path: Path) -> list:
    """Read all parse failures from a CSV log file.

    Args:
        log_path: Path to the CSV log file

    Returns:
        List of dictionaries, one per failure record
    """
    log_path = Path(log_path)

    if not log_path.exists():
        return []

    failures = []

    try:
        with open(log_path, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                failures.append(row)
    except Exception as e:
        logger = _get_logger()
        logger.error(f"Failed to read parse failures: {type(e).__name__}: {e}")
        raise

    return failures
