"""
Logging infrastructure for the Visual Motion Agency project.

Provides a centralized logging configuration that records:
- Data provenance (source, timestamp, checksum)
- Processing steps (input files, parameters, output files)
- System events and errors

Usage:
    from utils.logging_config import get_logger
    logger = get_logger('data_ingestion')
    logger.info("Starting data download")
"""
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import json

# Project root relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Ensure log directories exist
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Log format with timestamp, level, module, and message
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Global logger registry to avoid duplicate handlers
_logger_registry = {}

def get_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Get or create a logger with the specified name.
    
    Args:
        name: Logger name (e.g., 'data_ingestion', 'preprocessing')
        log_file: Optional filename relative to logs/ directory. 
                 If None, logs to 'project.log' by default.
        level: Logging level (default: INFO)
    
    Returns:
        Configured logging.Logger instance
    """
    if name in _logger_registry:
        return _logger_registry[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers if already configured
    if logger.handlers:
        _logger_registry[name] = logger
        return logger
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (default or specified)
    if log_file is None:
        log_file = "project.log"
    
    log_path = LOGS_DIR / log_file
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Add a special handler for provenance logs if requested
    if name.startswith("provenance"):
        provenance_handler = logging.FileHandler(LOGS_DIR / "provenance.log")
        provenance_handler.setLevel(logging.INFO)
        provenance_handler.setFormatter(formatter)
        logger.addHandler(provenance_handler)
    
    _logger_registry[name] = logger
    return logger

def log_provenance(source: str, destination: str, metadata: dict, logger_name: str = "provenance") -> None:
    """
    Log data provenance information.
    
    Args:
        source: Source file/path or data identifier
        destination: Destination file/path
        metadata: Dictionary containing provenance details (e.g., checksum, timestamp, parameters)
        logger_name: Name of the logger to use
    """
    logger = get_logger(logger_name)
    
    provenance_entry = {
        "timestamp": datetime.now().isoformat(),
        "source": str(source),
        "destination": str(destination),
        "metadata": metadata
    }
    
    # Log as JSON for machine readability
    logger.info(json.dumps(provenance_entry))

def log_processing_step(step_name: str, input_files: list, output_files: list, 
                       parameters: dict, logger_name: str = "processing") -> None:
    """
    Log a processing step with inputs, outputs, and parameters.
    
    Args:
        step_name: Name of the processing step
        input_files: List of input file paths
        output_files: List of output file paths
        parameters: Dictionary of parameters used
        logger_name: Name of the logger to use
    """
    logger = get_logger(logger_name)
    
    step_entry = {
        "timestamp": datetime.now().isoformat(),
        "step": step_name,
        "inputs": [str(f) for f in input_files],
        "outputs": [str(f) for f in output_files],
        "parameters": parameters
    }
    
    logger.info(f"Starting step: {step_name}")
    logger.info(json.dumps(step_entry))

def log_error(step_name: str, error: Exception, context: dict = None, logger_name: str = "errors") -> None:
    """
    Log an error with context.
    
    Args:
        step_name: Name of the step where error occurred
        error: Exception instance
        context: Optional dictionary of contextual information
        logger_name: Name of the logger to use
    """
    logger = get_logger(logger_name, level=logging.ERROR)
    
    error_entry = {
        "timestamp": datetime.now().isoformat(),
        "step": step_name,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context or {}
    }
    
    logger.error(f"Error in step: {step_name}")
    logger.error(json.dumps(error_entry))

# Initialize default loggers
get_logger("project")
get_logger("data_ingestion")
get_logger("preprocessing")
get_logger("modeling")
get_logger("visualization")
get_logger("errors")
get_logger("provenance")

__all__ = [
    "get_logger",
    "log_provenance",
    "log_processing_step",
    "log_error",
    "PROJECT_ROOT",
    "LOGS_DIR"
]
