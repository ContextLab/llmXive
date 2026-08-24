"""
Logging infrastructure for the llmXive automated science pipeline.

Provides timestamped, multi-level logging with error code tracking.
Integrates with loguru for structured output and file rotation.
"""
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Any
import json
import logging
from loguru import logger

# Global state for error tracking
_error_store: List[Dict[str, Any]] = []
_initialized: bool = False
_log_file_path: Optional[Path] = None

# Error code registry
ERROR_CODES = {
    101: "INSUFFICIENT_REPLICATES",
    102: "EXCESSIVE_REPLICATES",
    103: "ALIGNMENT_TIMEOUT",
    104: "DATA_FETCH_FAILED",
    105: "MANIFEST_VALIDATION_FAILED",
    106: "TREE_FILE_MISSING",
    107: "TREE_FILE_MALFORMED",
    108: "PHYLOP_QUERY_FAILED",
    109: "STATS_COMPUTATION_FAILED",
    110: "PLOT_VALIDATION_FAILED",
}

def setup_logger(
    log_dir: str = "data/logs",
    filename: str = "pipeline.log",
    level: str = "INFO",
    rotation: str = "10 MB",
    retention: str = "7 days",
) -> Path:
    """
    Initialize the logging infrastructure.
    
    Args:
        log_dir: Directory to store log files
        filename: Name of the log file
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        rotation: Max size before rotation (e.g., "10 MB")
        retention: How long to keep old logs (e.g., "7 days")
        
    Returns:
        Path to the created log file
        
    Raises:
        ValueError: If log_dir cannot be created
    """
    global _initialized, _log_file_path
    
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    log_file = log_path / filename
    _log_file_path = log_file
    
    # Remove default loguru handler
    logger.remove()
    
    # Add console handler with format
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
    )
    
    # Add file handler with rotation
    logger.add(
        str(log_file),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=level,
        rotation=rotation,
        retention=retention,
        compression="zip",
    )
    
    _initialized = True
    logger.info(f"Logger initialized. Log file: {log_file}")
    return log_file

def get_log_file_path() -> Optional[Path]:
    """Return the path to the current log file."""
    return _log_file_path

def track_error(
    error_code: int,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    exception: Optional[Exception] = None,
) -> Dict[str, Any]:
    """
    Track an error with code and context for audit trails.
    
    Args:
        error_code: Numeric error code from ERROR_CODES
        message: Human-readable error message
        context: Optional dictionary of contextual data
        exception: Optional exception object for traceback
        
    Returns:
        Dictionary containing the tracked error record
    """
    if not _initialized:
        setup_logger()
    
    error_record = {
        "timestamp": datetime.utcnow().isoformat(),
        "error_code": error_code,
        "error_name": ERROR_CODES.get(error_code, f"UNKNOWN_{error_code}"),
        "message": message,
        "context": context or {},
        "exception_type": type(exception).__name__ if exception else None,
        "exception_message": str(exception) if exception else None,
    }
    
    _error_store.append(error_record)
    
    # Log to loguru
    if exception:
        logger.error(f"[{error_record['error_name']}] {message}", exc_info=True)
    else:
        logger.error(f"[{error_record['error_name']}] {message}")
    
    return error_record

def get_tracked_errors() -> List[Dict[str, Any]]:
    """Return all tracked errors."""
    return _error_store.copy()

def get_error_summary() -> Dict[str, Any]:
    """
    Generate a summary of all tracked errors.
    
    Returns:
        Dictionary with error counts by code and total count
    """
    summary = {
        "total_errors": len(_error_store),
        "by_code": {},
        "by_name": {},
        "latest_error": _error_store[-1] if _error_store else None,
    }
    
    for error in _error_store:
        code = error["error_code"]
        name = error["error_name"]
        
        summary["by_code"][code] = summary["by_code"].get(code, 0) + 1
        summary["by_name"][name] = summary["by_name"].get(name, 0) + 1
    
    return summary

def log_error(
    error_code: int,
    message: str,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Convenience function to track and log an error.
    
    Args:
        error_code: Numeric error code
        message: Error message
        context: Optional context dictionary
    """
    track_error(error_code, message, context)

def log_critical(message: str, context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a critical error with context.
    
    Args:
        message: Critical error message
        context: Optional context dictionary
    """
    if not _initialized:
        setup_logger()
    
    logger.critical(f"[CRITICAL] {message}", extra={"context": context or {}})

def log_exception(
    error_code: int,
    message: str,
    exception: Exception,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an exception with traceback.
    
    Args:
        error_code: Numeric error code
        message: Error message
        exception: Exception object
        context: Optional context dictionary
    """
    track_error(error_code, message, context, exception)

def log_pipeline_step(step_name: str, status: str = "STARTED") -> None:
    """
    Log a pipeline step lifecycle event.
    
    Args:
        step_name: Name of the pipeline step
        status: One of STARTED, COMPLETED, FAILED
    """
    if not _initialized:
        setup_logger()
    
    status_icon = {
        "STARTED": "▶",
        "COMPLETED": "✓",
        "FAILED": "✗",
    }.get(status, "?")
    
    logger.info(f"{status_icon} PIPELINE_STEP: {step_name} [{status}]")

def export_error_log(output_path: str = "data/logs/error_log.json") -> Path:
    """
    Export all tracked errors to a JSON file.
    
    Args:
        output_path: Path for the output JSON file
        
    Returns:
        Path to the created file
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    
    summary = get_error_summary()
    export_data = {
        "exported_at": datetime.utcnow().isoformat(),
        "summary": summary,
        "errors": _error_store,
    }
    
    with open(output, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, default=str)
    
    logger.info(f"Error log exported to {output}")
    return output

def quick_log(level: str, message: str) -> None:
    """
    Quick log without error tracking.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Message to log
    """
    if not _initialized:
        setup_logger()
    
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(message)

def clean_error_store() -> None:
    """Clear the error store (useful for testing)."""
    global _error_store
    _error_store.clear()

def log_hash_to_file(
    file_path: str,
    hash_value: str,
    algorithm: str = "sha256",
) -> None:
    """
    Log a file hash to the pipeline log.
    
    Args:
        file_path: Path to the hashed file
        hash_value: The hash string
        algorithm: Hash algorithm used
    """
    if not _initialized:
        setup_logger()
    
    logger.info(f"HASH: {file_path} | {algorithm}: {hash_value}")

def log_manifest_entry(
    artifact_name: str,
    hash_value: str,
    artifact_type: str,
    size_bytes: Optional[int] = None,
) -> None:
    """
    Log a manifest entry to the pipeline log.
    
    Args:
        artifact_name: Name of the artifact
        hash_value: SHA-256 hash
        artifact_type: Type of artifact (e.g., 'BAM', 'PSI_TABLE')
        size_bytes: Optional file size in bytes
    """
    if not _initialized:
        setup_logger()
    
    entry = f"MANIFEST: {artifact_name} | type={artifact_type} | hash={hash_value}"
    if size_bytes is not None:
        entry += f" | size={size_bytes}B"
    
    logger.info(entry)

# Initialize logger on module import if needed
# Note: Explicit setup_logger() call is recommended in main entry points
# This ensures the logger is ready for immediate use in imports