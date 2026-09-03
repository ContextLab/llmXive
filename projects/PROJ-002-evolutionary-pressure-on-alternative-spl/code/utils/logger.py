import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from loguru import logger

# Global error store for tracking errors across the pipeline
_error_store: List[Dict[str, Any]] = []
_log_file_path: Optional[Path] = None

def setup_logger(log_dir: Optional[Union[str, Path]] = None, level: str = "INFO") -> Path:
    """
    Initialize the logging infrastructure.

    Args:
        log_dir: Directory to store log files. Defaults to 'logs' in current working dir.
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    Returns:
        Path to the created log file.
    """
    global _log_file_path

    if log_dir is None:
        log_dir = Path.cwd() / "logs"
    else:
        log_dir = Path(log_dir)

    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"pipeline_{timestamp}.log"
    log_path = log_dir / log_filename
    _log_file_path = log_path

    # Remove default handlers to avoid duplicates
    logger.remove()

    # Add console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=level
    )

    # Add file handler
    logger.add(
        log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} | {message}",
        level=level,
        rotation="10 MB",
        retention="1 week"
    )

    logger.info(f"Logger initialized. Log file: {log_path}")
    return log_path

def get_log_file_path() -> Optional[Path]:
    """Return the path to the current log file."""
    return _log_file_path

def track_error(error_code: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Record an error in the global error store.

    Args:
        error_code: A unique code for the error (e.g., 'E001').
        message: Human-readable error message.
        context: Optional dictionary of additional context (e.g., file paths, variables).
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "error_code": error_code,
        "message": message,
        "context": context or {}
    }
    _error_store.append(entry)
    logger.error(f"[{error_code}] {message}")

def get_tracked_errors() -> List[Dict[str, Any]]:
    """Return the list of tracked errors."""
    return _error_store.copy()

def get_error_summary() -> Dict[str, int]:
    """
    Return a summary of error counts by error code.

    Returns:
        Dictionary mapping error_code to count.
    """
    summary = {}
    for entry in _error_store:
        code = entry["error_code"]
        summary[code] = summary.get(code, 0) + 1
    return summary

def log_error(error_code: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an error and track it.

    Args:
        error_code: Unique error code.
        message: Error message.
        context: Optional context.
    """
    track_error(error_code, message, context)
    logger.error(f"[{error_code}] {message}")

def log_critical(error_code: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a critical error and track it.

    Args:
        error_code: Unique error code.
        message: Error message.
        context: Optional context.
    """
    track_error(error_code, message, context)
    logger.critical(f"[{error_code}] {message}")

def log_exception(error_code: str, exc: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an exception and track it.

    Args:
        error_code: Unique error code.
        exc: The exception object.
        context: Optional context.
    """
    track_error(error_code, str(exc), context)
    logger.exception(f"[{error_code}] Exception occurred: {exc}")

def log_pipeline_step(step_name: str, status: str = "started", details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log the start or completion of a pipeline step.

    Args:
        step_name: Name of the step.
        status: 'started', 'completed', 'failed'.
        details: Optional details about the step.
    """
    msg = f"Pipeline Step: {step_name} - {status}"
    if details:
        msg += f" | Details: {json.dumps(details)}"
    if status == "completed":
        logger.info(msg)
    elif status == "failed":
        logger.error(msg)
    else:
        logger.info(msg)

def export_error_log(output_path: Union[str, Path]) -> None:
    """
    Export the error store to a JSON file.

    Args:
        output_path: Path to the output JSON file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(_error_store, f, indent=2)
    logger.info(f"Error log exported to {output_path}")

def quick_log(message: str, level: str = "INFO") -> None:
    """
    Log a simple message without extra formatting.

    Args:
        message: Message to log.
        level: Log level string.
    """
    getattr(logger, level.lower())(message)

def clean_error_store() -> None:
    """Clear the global error store."""
    global _error_store
    _error_store = []
    logger.debug("Error store cleared.")

# Import Union here to avoid forward reference issues if type hints are evaluated
from typing import Union
