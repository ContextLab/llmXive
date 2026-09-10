import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import json

# Ensure the logs directory exists relative to project root
# We assume the project root is the parent of the 'code' directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_LOG_DIR = _PROJECT_ROOT / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Log file naming convention: YYYYMMDD_HHMMSS_<process_id>.log
# This ensures unique files for parallel runs or re-runs
_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
_LOG_FILE = _LOG_DIR / f"pipeline_{_TIMESTAMP}.log"

# Global logger instance
_logger: Optional[logging.Logger] = None

def _get_file_handler() -> logging.FileHandler:
    """Creates a file handler with JSON-like structured formatting for provenance."""
    fh = logging.FileHandler(_LOG_FILE)
    fh.setLevel(logging.INFO)
    # Custom format to include timestamp, level, module, and message
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    return fh

def _get_console_handler() -> logging.StreamHandler:
    """Creates a console handler for immediate feedback."""
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    ch.setFormatter(formatter)
    return ch

def get_logger(name: str = "llmXive.pipeline") -> logging.Logger:
    """
    Returns a configured logger instance.
    Initializes the logger with file and console handlers if not already done.
    """
    global _logger
    
    if _logger is None:
        _logger = logging.getLogger(name)
        _logger.setLevel(logging.DEBUG)
        
        # Avoid adding handlers multiple times if called repeatedly
        if not _logger.handlers:
            _logger.addHandler(_get_file_handler())
            _logger.addHandler(_get_console_handler())
    
    # Return a child logger for the specific module
    return logging.getLogger(f"{name}.{name.split('.')[-1]}")

def log_provenance(
    step_name: str, 
    input_sources: Dict[str, str], 
    output_targets: Dict[str, str], 
    parameters: Optional[Dict[str, Any]] = None,
    logger_name: str = "llmXive.pipeline"
) -> None:
    """
    Logs data provenance: what data was used, what was produced, and with what parameters.
    This is critical for reproducibility and auditing.
    """
    log = get_logger(logger_name)
    
    msg_parts = [
        f"PROVENANCE: {step_name}",
        f"Inputs: {json.dumps(input_sources)}",
        f"Outputs: {json.dumps(output_targets)}"
    ]
    
    if parameters:
        msg_parts.append(f"Params: {json.dumps(parameters)}")
    
    log.info(" | ".join(msg_parts))

def log_processing_step(
    step_name: str,
    status: str,
    details: Optional[str] = None,
    duration_seconds: Optional[float] = None,
    logger_name: str = "llmXive.pipeline"
) -> None:
    """
    Logs the execution status of a specific processing step.
    """
    log = get_logger(logger_name)
    
    msg = f"STEP: {step_name} | Status: {status}"
    if details:
        msg += f" | Details: {details}"
    if duration_seconds is not None:
        msg += f" | Duration: {duration_seconds:.2f}s"
    
    if status == "FAILED":
        log.error(msg)
    elif status == "COMPLETED":
        log.info(msg)
    else:
        log.debug(msg)

def log_error(
    step_name: str,
    error_type: str,
    error_message: str,
    traceback_str: Optional[str] = None,
    logger_name: str = "llmXive.pipeline"
) -> None:
    """
    Logs a specific error event with context.
    """
    log = get_logger(logger_name)
    
    msg = f"ERROR: {step_name} | Type: {error_type} | Message: {error_message}"
    if traceback_str:
        msg += f" | Traceback: {traceback_str}"
    
    log.critical(msg)