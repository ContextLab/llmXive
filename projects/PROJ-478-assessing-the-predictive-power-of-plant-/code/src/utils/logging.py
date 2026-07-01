"""
Structured logging and provenance tracking for llmXive research pipeline.

This module provides a centralized logging configuration that ensures:
1. Consistent log formatting across all project modules
2. Provenance tracking (who, when, what, parameters)
3. Structured JSON output for machine parsing
4. Dual output to console and file
"""

import logging
import json
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# Import project constants
import src.utils.config as config

# Module-level logger instance
_logger: Optional[logging.Logger] = None
_initialized: bool = False

# Log file path (relative to project root)
LOG_DIR = Path("data/logs")
LOG_FILENAME = "pipeline.log"

# JSON formatter for structured logging
class JsonFormatter(logging.Formatter):
    """Custom formatter that outputs log records as JSON."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, "provenance"):
            log_entry["provenance"] = record.provenance
        if hasattr(record, "task_id"):
            log_entry["task_id"] = record.task_id
        if hasattr(record, "species"):
            log_entry["species"] = record.species
        if hasattr(record, "parameters"):
            log_entry["parameters"] = record.parameters
        if hasattr(record, "data_source"):
            log_entry["data_source"] = record.data_source
        if hasattr(record, "error"):
            log_entry["error"] = str(record.error)
        if hasattr(record, "exception"):
            log_entry["exception"] = record.exc_info[0].__name__ if record.exc_info else None
            log_entry["exception_traceback"] = self.formatException(record.exc_info) if record.exc_info else None
        
        return json.dumps(log_entry)

class ProvenanceAdapter(logging.Filter):
    """Filter to inject provenance metadata into log records."""
    
    def __init__(self, provenance: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.provenance = provenance or {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        # Inject global provenance if available
        if hasattr(config, "GLOBAL_PROVENANCE"):
            record.provenance = {
                **getattr(config, "GLOBAL_PROVENANCE", {}),
                **self.provenance,
            }
        else:
            record.provenance = self.provenance
        return True

def setup_logging(
    level: Optional[int] = None,
    log_file: Optional[Path] = None,
    json_format: bool = False,
    provenance: Optional[Dict[str, Any]] = None,
) -> logging.Logger:
    """
    Configure and return the project logger.
    
    Args:
        level: Logging level (default: config.LOG_LEVEL or logging.INFO)
        log_file: Path to log file (default: data/logs/pipeline.log)
        json_format: If True, use JSON formatting; else use human-readable format
        provenance: Initial provenance metadata to attach to all logs
    
    Returns:
        Configured logger instance
    """
    global _logger, _initialized
    
    if _initialized:
        return _logger
    
    # Determine log level
    if level is None:
        level = getattr(config, "LOG_LEVEL", logging.INFO)
    
    # Create log directory if it doesn't exist
    log_path = log_file if log_file else LOG_DIR / LOG_FILENAME
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    _logger = logging.getLogger("llmXive")
    _logger.setLevel(level)
    _logger.propagate = False
    
    # Clear existing handlers
    _logger.handlers.clear()
    
    # Console handler with human-readable format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    _logger.addHandler(console_handler)
    
    # File handler (JSON format for machine parsing)
    file_handler = logging.FileHandler(log_path, mode='a')
    file_handler.setLevel(level)
    
    if json_format:
        file_handler.setFormatter(JsonFormatter())
    else:
        file_handler.setFormatter(console_format)
    
    _logger.addHandler(file_handler)
    
    # Add provenance filter if provided
    if provenance:
        provenance_filter = ProvenanceAdapter(provenance)
        _logger.addFilter(provenance_filter)
    
    _initialized = True
    
    _logger.info(
        "Logging initialized",
        extra={
            "parameters": {
                "level": logging.getLevelName(level),
                "log_file": str(log_path),
                "json_format": json_format,
            }
        }
    )
    
    return _logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get the project logger, initializing it if necessary.
    
    Args:
        name: Optional name for a child logger (e.g., "llmXive.data")
    
    Returns:
        Logger instance
    """
    global _logger
    
    if _logger is None:
        _logger = setup_logging()
    
    if name:
        return _logger.getChild(name)
    return _logger

def log_provenance(
    task_id: str,
    action: str,
    data_source: Optional[str] = None,
    species: Optional[str] = None,
    parameters: Optional[Dict[str, Any]] = None,
    level: int = logging.INFO,
) -> None:
    """
    Log a provenance event with structured metadata.
    
    Args:
        task_id: Identifier for the current task (e.g., "T005")
        action: Description of the action performed
        data_source: Source of the data being processed
        species: Species name if applicable
        parameters: Additional parameters for the action
        level: Logging level
    """
    logger = get_logger()
    
    extra = {
        "task_id": task_id,
    }
    
    if data_source:
        extra["data_source"] = data_source
    if species:
        extra["species"] = species
    if parameters:
        extra["parameters"] = parameters
    
    logger.log(level, action, extra=extra)

def log_error(
    message: str,
    error: Exception,
    task_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log an error with full exception details.
    
    Args:
        message: Error message
        error: Exception instance
        task_id: Current task identifier
        context: Additional context information
    """
    logger = get_logger()
    
    extra = {"error": error}
    if task_id:
        extra["task_id"] = task_id
    if context:
        extra["parameters"] = context
    
    logger.exception(message, extra=extra)