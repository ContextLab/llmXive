"""
Logging infrastructure for llmXive pipeline.

Provides timestamped, multi-level logging with error code tracking.
Uses loguru for structured logging and file rotation.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
import json

from loguru import logger

# Global state for error tracking
_tracked_errors: List[Dict[str, Any]] = []
_log_file_path: Optional[Path] = None
_initialized: bool = False


def setup_logger(
    log_dir: str = "data/logs",
    log_file: str = "pipeline.log",
    level: str = "DEBUG",
    rotation: str = "500 MB",
    retention: str = "7 days",
    compression: str = "gz"
) -> Path:
    """
    Configure the logger instance with file and console handlers.

    Args:
        log_dir: Directory to store log files
        log_file: Name of the log file
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        rotation: Max size before rotation
        retention: How long to keep old logs
        compression: Compression format for rotated logs

    Returns:
        Path to the log file
    """
    global _initialized, _log_file_path

    # Ensure log directory exists
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    full_log_path = log_path / log_file
    _log_file_path = full_log_path

    # Remove default handler if exists
    logger.remove()

    # Add console handler with color and format
    logger.add(
        sys.stdout,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )

    # Add file handler with rotation and detailed format
    logger.add(
        str(full_log_path),
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation=rotation,
        retention=retention,
        compression=compression,
        enqueue=True  # Thread-safe
    )

    _initialized = True
    logger.info(f"Logger initialized. Log file: {full_log_path}")

    return full_log_path


def track_error(
    error_code: str,
    error_message: str,
    context: Optional[Dict[str, Any]] = None,
    severity: str = "ERROR"
) -> Dict[str, Any]:
    """
    Track an error with a specific error code for audit trails.

    Args:
        error_code: Unique identifier for this error type (e.g., "E101")
        error_message: Human-readable error description
        context: Additional context data (optional)
        severity: Error severity level

    Returns:
        Dictionary containing the tracked error info
    """
    error_entry = {
        "timestamp": datetime.now().isoformat(),
        "error_code": error_code,
        "error_message": error_message,
        "severity": severity,
        "context": context or {}
    }

    _tracked_errors.append(error_entry)

    # Log to the main logger as well
    log_level = getattr(logger, severity.lower(), logger.error)
    log_level(f"[{error_code}] {error_message}")
    if context:
        log_level(f"Context: {context}")

    return error_entry


def get_tracked_errors() -> List[Dict[str, Any]]:
    """
    Retrieve all tracked errors.

    Returns:
        List of all tracked error dictionaries
    """
    return _tracked_errors.copy()


def log_error(error_code: str, message: str, exc_info: bool = False) -> None:
    """
    Log an error with a specific error code.

    Args:
        error_code: Unique error identifier
        message: Error message
        exc_info: Whether to include exception info
    """
    logger.error(f"[{error_code}] {message}")
    if exc_info:
        logger.opt(exception=True).error("Exception details")


def log_critical(error_code: str, message: str) -> None:
    """
    Log a critical error that may halt execution.

    Args:
        error_code: Unique error identifier
        message: Critical error message
    """
    logger.critical(f"[{error_code}] {message}")
    track_error(error_code, message, severity="CRITICAL")


def log_exception(error_code: str, message: str, exc: Exception) -> None:
    """
    Log an exception with full traceback.

    Args:
        error_code: Unique error identifier
        message: Error message
        exc: The exception object
    """
    logger.opt(exception=True).error(f"[{error_code}] {message}")
    track_error(error_code, str(exc), context={"exception_type": type(exc).__name__}, severity="ERROR")


def log_pipeline_step(step_name: str, message: str, duration: Optional[float] = None) -> None:
    """
    Log a pipeline step with optional duration.

    Args:
        step_name: Name of the pipeline step
        message: Description of the step
        duration: Optional execution duration in seconds
    """
    log_msg = f"STEP: {step_name} - {message}"
    if duration is not None:
        log_msg += f" (duration: {duration:.2f}s)"
    logger.info(log_msg)


def get_log_file_path() -> Optional[Path]:
    """
    Get the path to the current log file.

    Returns:
        Path to log file or None if not initialized
    """
    return _log_file_path


def get_error_summary() -> str:
    """
    Generate a summary of all tracked errors.

    Returns:
        Formatted string summary of errors
    """
    if not _tracked_errors:
        return "No errors tracked."

    summary_lines = [
        "=== ERROR SUMMARY ===",
        f"Total errors: {len(_tracked_errors)}",
        ""
    ]

    # Group by error code
    error_counts: Dict[str, int] = {}
    for err in _tracked_errors:
        code = err["error_code"]
        error_counts[code] = error_counts.get(code, 0) + 1

    summary_lines.append("Errors by code:")
    for code, count in sorted(error_counts.items()):
        summary_lines.append(f"  {code}: {count} occurrence(s)")

    summary_lines.append("")
    summary_lines.append("Detailed errors:")
    for i, err in enumerate(_tracked_errors, 1):
        summary_lines.append(f"{i}. [{err['error_code']}] {err['error_message']}")
        if err.get('context'):
            summary_lines.append(f"   Context: {err['context']}")

    return "\n".join(summary_lines)


def export_error_log(output_path: str) -> Path:
    """
    Export all tracked errors to a JSON file.

    Args:
        output_path: Path to write the error log

    Returns:
        Path to the written file
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(_tracked_errors, f, indent=2, default=str)

    logger.info(f"Error log exported to: {output_file}")
    return output_file


# Convenience function for immediate logging without setup
def quick_log(message: str, level: str = "INFO") -> None:
    """
    Quick logging without explicit setup.

    Args:
        message: Message to log
        level: Log level
    """
    if not _initialized:
        # Initialize with defaults if not already done
        setup_logger()

    log_method = getattr(logger, level.lower(), logger.info)
    log_method(message)
