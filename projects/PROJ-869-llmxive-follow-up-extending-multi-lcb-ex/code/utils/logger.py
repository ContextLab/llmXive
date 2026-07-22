"""
Logging utilities for the llmXive pipeline.
Provides structured logging with file and console handlers,
including error tracking and JSON-formatted logs for automated analysis.
"""
import logging
import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from code.config import config

# Custom log record factory to include extra context if needed
class ContextLogRecord(logging.LogRecord):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure standard attributes exist
        if not hasattr(self, 'task_id'):
            self.task_id = None
        if not hasattr(self, 'component'):
            self.component = None

def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_file: Optional path to a log file. If None, logs to stderr.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
    """
    # Create a root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers = []

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # File Handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: The name of the logger (usually __name__).
            
    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # If no handlers are set up yet, set up default console logging
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def log_error_to_file(error_details: Dict[str, Any], log_path: Optional[Path] = None) -> None:
    """
    Log error details to a dedicated JSON error log file for structured analysis.
    
    Args:
        error_details: Dictionary containing error information (message, traceback, context).
        log_path: Optional path to the error log file. Defaults to data/logs/errors.json.
    """
    if log_path is None:
        log_path = config.ERROR_LOG_PATH
    
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing errors if file exists
    existing_errors = []
    if log_path.exists():
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    # Handle JSON Lines format or single JSON array
                    if content.startswith('['):
                        existing_errors = json.loads(content)
                    else:
                        # Treat as JSONL
                        for line in content.split('\n'):
                            if line.strip():
                                existing_errors.append(json.loads(line))
        except (json.JSONDecodeError, IOError) as e:
            logger = get_logger(__name__)
            logger.warning(f"Could not read existing error log: {e}")
            existing_errors = []
    
    # Append new error
    # Add timestamp if not present
    if 'timestamp' not in error_details:
        error_details['timestamp'] = logging.Formatter('%Y-%m-%d %H:%M:%S').format(logging.LogRecord(
            name='', level=0, pathname='', lineno=0, msg='', args=(), exc_info=None
        ))
    
    existing_errors.append(error_details)
    
    # Write back
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(existing_errors, f, indent=2)

def log_execution_failure(task_id: str, error_msg: str, traceback_str: Optional[str] = None) -> None:
    """
    Convenience function to log a pipeline execution failure.
    
    Args:
        task_id: The ID of the failed task (e.g., 'T007').
        error_msg: The error message.
        traceback_str: Optional full traceback string.
    """
    error_details = {
        "task_id": task_id,
        "error_type": "ExecutionFailure",
        "message": error_msg,
        "traceback": traceback_str,
        "severity": "CRITICAL"
    }
    log_error_to_file(error_details)
    logger = get_logger(__name__)
    logger.critical(f"Task {task_id} failed: {error_msg}")
    if traceback_str:
        logger.debug(traceback_str)

# Initialize logging with a default file if needed, or just console
# For now, we rely on get_logger to initialize on demand, but we can call setup_logging here if desired.
# setup_logging() 
