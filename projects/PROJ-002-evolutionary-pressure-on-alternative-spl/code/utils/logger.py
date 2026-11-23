import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from loguru import logger

# Global error store for tracking pipeline failures
_error_store: List[Dict[str, Any]] = []
_log_file_path: Optional[Path] = None

def setup_logger(log_dir: str = "data", log_file: str = "pipeline.log") -> Path:
    """
    Initialize the logging infrastructure per FR-009.
    
    Configures loguru to write to a timestamped file and stdout.
    Captures timestamps, exit codes, and step summaries.
    
    Args:
        log_dir: Directory to store log files (default: 'data')
        log_file: Base name for the log file (default: 'pipeline.log')
        
    Returns:
        Path to the created log file
    """
    global _log_file_path
    
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Create a timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_log_name = f"{log_file.replace('.log', '')}_{timestamp}.log"
    _log_file_path = log_path / full_log_name
    
    # Remove existing handlers to avoid duplicates
    logger.remove()
    
    # Add stdout handler with detailed formatting
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Add file handler with detailed formatting for audit trail
    logger.add(
        _log_file_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="10 days",
        compression="gz"
    )
    
    logger.info(f"Logging infrastructure initialized. Log file: {_log_file_path}")
    return _log_file_path

def get_log_file_path() -> Optional[Path]:
    """Return the path to the current log file."""
    return _log_file_path

def track_error(error_type: str, message: str, step: str = "unknown", details: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Track an error in the global error store for audit trails.
    
    Args:
        error_type: Type of error (e.g., 'DownloadError', 'AlignmentError')
        message: Human-readable error message
        step: Pipeline step where error occurred
        details: Optional dictionary of additional context
        
    Returns:
        The recorded error dictionary
    """
    error_entry = {
        "timestamp": datetime.now().isoformat(),
        "error_type": error_type,
        "message": message,
        "step": step,
        "details": details or {},
        "exit_code": 1
    }
    _error_store.append(error_entry)
    logger.error(f"[{step}] {error_type}: {message}")
    return error_entry

def get_tracked_errors() -> List[Dict[str, Any]]:
    """Return all tracked errors."""
    return _error_store.copy()

def get_error_summary() -> Dict[str, Any]:
    """
    Generate a summary of all tracked errors.
    
    Returns:
        Dictionary with error counts and last error details
    """
    if not _error_store:
        return {"total_errors": 0, "errors": []}
    
    error_types = {}
    for err in _error_store:
        et = err.get("error_type", "Unknown")
        error_types[et] = error_types.get(et, 0) + 1
    
    return {
        "total_errors": len(_error_store),
        "error_types": error_types,
        "last_error": _error_store[-1]
    }

def log_error(step: str, message: str, exit_code: int = 1, exception: Optional[Exception] = None) -> None:
    """
    Log a critical error with exit code and step summary.
    
    Args:
        step: Pipeline step name
        message: Error message
        exit_code: Exit code to be used if script terminates
        exception: Optional exception object for traceback
    """
    error_details = {}
    if exception:
        error_details["exception_type"] = type(exception).__name__
        error_details["exception_message"] = str(exception)
        import traceback
        error_details["traceback"] = traceback.format_exc()
    
    track_error(
        error_type="PipelineError",
        message=f"{step}: {message}",
        step=step,
        details=error_details
    )
    
    logger.critical(f"Step '{step}' failed with exit code {exit_code}: {message}")

def log_critical(step: str, message: str, exit_code: int = 1) -> None:
    """
    Log a critical failure that should abort the pipeline.
    
    Args:
        step: Pipeline step name
        message: Critical error message
        exit_code: Exit code for termination
    """
    log_error(step, message, exit_code)
    # Note: This does not exit; caller must call sys.exit() if needed

def log_exception(step: str, message: str, exception: Exception, exit_code: int = 1) -> None:
    """
    Log an exception with full traceback.
    
    Args:
        step: Pipeline step name
        message: Context message
        exception: The exception object
        exit_code: Exit code for termination
    """
    log_error(step, message, exit_code, exception)

def log_pipeline_step(step_name: str, status: str, duration_seconds: Optional[float] = None, summary: Optional[str] = None) -> None:
    """
    Log a pipeline step completion with timestamp and summary.
    
    Args:
        step_name: Name of the pipeline step
        status: 'STARTED', 'COMPLETED', 'FAILED', or 'SKIPPED'
        duration_seconds: Optional duration of the step
        summary: Optional summary of results (e.g., "Downloaded 12 files")
    """
    timestamp = datetime.now().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "step": step_name,
        "status": status,
        "duration_seconds": duration_seconds,
        "summary": summary
    }
    
    if status == "STARTED":
        logger.info(f"Step '{step_name}' started at {timestamp}")
    elif status == "COMPLETED":
        duration_str = f" (took {duration_seconds:.2f}s)" if duration_seconds else ""
        summary_str = f" - {summary}" if summary else ""
        logger.info(f"Step '{step_name}' completed{duration_str}{summary_str}")
    elif status == "FAILED":
        logger.error(f"Step '{step_name}' failed{duration_str if duration_seconds else ''}")
    elif status == "SKIPPED":
        logger.warning(f"Step '{step_name}' was skipped")
    
    # Also log to a structured JSON file for easy parsing
    if _log_file_path:
        structured_log_path = _log_file_path.parent / f"{_log_file_path.stem}_structured.json"
        try:
            if structured_log_path.exists():
                with open(structured_log_path, 'r') as f:
                    structured_logs = json.load(f)
            else:
                structured_logs = []
            
            structured_logs.append(log_entry)
            
            with open(structured_log_path, 'w') as f:
                json.dump(structured_logs, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write structured log: {e}")

def export_error_log(output_path: Optional[Path] = None) -> Path:
    """
    Export the current error store to a JSON file.
    
    Args:
        output_path: Optional path to write the error log. Defaults to data/error_log.json
        
    Returns:
        Path to the written file
    """
    if output_path is None:
        output_path = Path("data") / "error_log.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    summary = get_error_summary()
    export_data = {
        "exported_at": datetime.now().isoformat(),
        "summary": summary,
        "errors": get_tracked_errors()
    }
    
    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    logger.info(f"Error log exported to {output_path}")
    return output_path

def quick_log(step: str, message: str, level: str = "INFO") -> None:
    """
    Quick logging wrapper for simple messages.
    
    Args:
        step: Pipeline step name
        message: Message to log
        level: Log level (INFO, WARNING, ERROR, CRITICAL)
    """
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(f"[{step}] {message}")

def clean_error_store() -> None:
    """Clear the global error store."""
    global _error_store
    _error_store = []
    logger.debug("Error store cleared")

def log_hash_to_file(file_path: Path, hash_value: str, step: str = "hashing") -> None:
    """
    Log a file hash to the structured log for audit trails.
    
    Args:
        file_path: Path to the file that was hashed
        hash_value: The computed hash value
        step: Pipeline step name
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "step": step,
        "action": "hash_recorded",
        "file_path": str(file_path),
        "hash_value": hash_value
    }
    
    logger.info(f"[{step}] Recorded hash for {file_path.name}: {hash_value}")
    
    if _log_file_path:
        structured_log_path = _log_file_path.parent / f"{_log_file_path.stem}_structured.json"
        try:
            if structured_log_path.exists():
                with open(structured_log_path, 'r') as f:
                    structured_logs = json.load(f)
            else:
                structured_logs = []
            
            structured_logs.append(log_entry)
            
            with open(structured_log_path, 'w') as f:
                json.dump(structured_logs, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write structured log: {e}")

def log_manifest_entry(manifest_path: Path, step: str = "manifest") -> None:
    """
    Log a manifest file creation to the structured log.
    
    Args:
        manifest_path: Path to the created manifest
        step: Pipeline step name
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "step": step,
        "action": "manifest_created",
        "manifest_path": str(manifest_path)
    }
    
    logger.info(f"[{step}] Manifest created: {manifest_path}")
    
    if _log_file_path:
        structured_log_path = _log_file_path.parent / f"{_log_file_path.stem}_structured.json"
        try:
            if structured_log_path.exists():
                with open(structured_log_path, 'r') as f:
                    structured_logs = json.load(f)
            else:
                structured_logs = []
            
            structured_logs.append(log_entry)
            
            with open(structured_log_path, 'w') as f:
                json.dump(structured_logs, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write structured log: {e}")