import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import json

# Define the log directory relative to project root
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Global logger instance
_logger: Optional[logging.Logger] = None

def get_logger(name: str = "llmXive_pipeline") -> logging.Logger:
    """
    Returns a configured logger instance.
    Creates the logger only once and reuses it on subsequent calls.
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger(name)
        _logger.setLevel(logging.DEBUG)

        if not _logger.handlers:
            # Console Handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            console_handler.setFormatter(console_formatter)
            _logger.addHandler(console_handler)

            # File Handler (Rotating)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file_path = LOG_DIR / f"pipeline_{timestamp}.log"
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            file_handler.setFormatter(file_formatter)
            _logger.addHandler(file_handler)

    return _logger

def log_provenance(step_name: str, input_source: str, output_target: str, details: Optional[dict] = None) -> None:
    """
    Logs data provenance information for audit trails.
    Records where data came from, what step processed it, and where it went.
    """
    logger = get_logger()
    timestamp = datetime.now().isoformat()
    
    log_entry = {
        "timestamp": timestamp,
        "event_type": "PROVENANCE",
        "step": step_name,
        "input_source": input_source,
        "output_target": output_target,
        "details": details or {}
    }
    
    logger.info(f"PROVENANCE: {json.dumps(log_entry)}")

def log_processing_step(step_name: str, status: str, metrics: Optional[dict] = None) -> None:
    """
    Logs the status of a specific processing step.
    Status can be 'START', 'COMPLETE', 'WARN', 'FAIL'.
    """
    logger = get_logger()
    timestamp = datetime.now().isoformat()
    
    log_entry = {
        "timestamp": timestamp,
        "event_type": "PROCESSING_STEP",
        "step": step_name,
        "status": status,
        "metrics": metrics or {}
    }
    
    if status == "FAIL":
        logger.error(f"STEP_FAIL: {json.dumps(log_entry)}")
    elif status == "WARN":
        logger.warning(f"STEP_WARN: {json.dumps(log_entry)}")
    else:
        logger.info(f"STEP_{status}: {json.dumps(log_entry)}")

def log_error(step_name: str, error_message: str, error_type: str, traceback_str: Optional[str] = None) -> None:
    """
    Logs a structured error event.
    """
    logger = get_logger()
    timestamp = datetime.now().isoformat()
    
    log_entry = {
        "timestamp": timestamp,
        "event_type": "ERROR",
        "step": step_name,
        "error_type": error_type,
        "error_message": error_message,
        "traceback": traceback_str
    }
    
    logger.error(f"ERROR_LOG: {json.dumps(log_entry)}")
    
    # Also write a dedicated error file for easy retrieval
    error_log_path = LOG_DIR / f"errors_{datetime.now().strftime('%Y%m%d')}.jsonl"
    with open(error_log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")