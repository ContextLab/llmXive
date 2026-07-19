"""
Base logging infrastructure and error handling for the metallic glasses pipeline.

This module provides:
- Custom exception hierarchy for specific pipeline failure modes.
- A centralized logger configuration that writes to both console and file.
- Context managers and decorators for robust error handling.
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
import traceback

# --- Custom Exception Hierarchy ---

class PipelineError(Exception):
    """Base class for all pipeline-specific errors."""
    def __init__(self, message: str, context: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()

class DataDownloadError(PipelineError):
    """Raised when dataset download fails (e.g., network, auth, schema mismatch)."""
    pass

class DataIngestionError(PipelineError):
    """Raised when CSV parsing, normalization, or validation fails."""
    pass

class FeatureEngineeringError(PipelineError):
    """Raised when feature computation (pymatgen, etc.) fails."""
    pass

class ModelTrainingError(PipelineError):
    """Raised when model training, validation, or selection fails."""
    pass

class ScreeningError(PipelineError):
    """Raised when candidate generation, prediction, or ranking fails."""
    pass

class ConfigurationError(PipelineError):
    """Raised when configuration loading or validation fails."""
    pass

# --- Logger Configuration ---

_logger_instance: Optional[logging.Logger] = None

def get_logger(name: str = "metallic_glasses_pipeline") -> logging.Logger:
    """
    Returns a configured logger instance.
    Ensures a single configuration per process to avoid duplicate handlers.
    """
    global _logger_instance

    if _logger_instance is not None and _logger_instance.name == name:
        return _logger_instance

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent adding handlers if already configured (e.g., in tests)
    if logger.handlers:
        _logger_instance = logger
        return logger

    # Create log directory if it doesn't exist
    log_dir = Path("state/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"pipeline_{timestamp}.log"

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # File Handler (All logs)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Error File Handler (Errors only)
    error_log_file = log_dir / f"errors_{timestamp}.log"
    error_handler = logging.FileHandler(error_log_file)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)

    _logger_instance = logger
    return logger

# --- Helper Functions ---

def log_pipeline_start(config_summary: Optional[dict] = None):
    """Logs the start of the pipeline execution."""
    logger = get_logger()
    logger.info("=" * 80)
    logger.info("PIPELINE EXECUTION STARTED")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    if config_summary:
        logger.info(f"Configuration: {config_summary}")
    logger.info("=" * 80)

def log_pipeline_end(status: str = "SUCCESS"):
    """Logs the completion of the pipeline execution."""
    logger = get_logger()
    logger.info("=" * 80)
    logger.info(f"PIPELINE EXECUTION COMPLETED: {status}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")
    logger.info("=" * 80)

def handle_pipeline_error(error: Exception, context: Optional[dict] = None):
    """
    Centralized error handler for pipeline failures.
    Logs the error with full traceback and raises a wrapped PipelineError if needed.
    """
    logger = get_logger()
    error_type = type(error).__name__
    error_msg = str(error)
    full_traceback = traceback.format_exc()

    # Log based on error type
    if isinstance(error, PipelineError):
        logger.error(f"Pipeline Error [{error_type}]: {error_msg}", exc_info=False)
        if error.context:
            logger.error(f"Context: {error.context}")
    else:
        logger.critical(f"Unexpected Error [{error_type}]: {error_msg}")
    
    logger.debug(f"Traceback:\n{full_traceback}")
    
    # Re-raise as a generic PipelineError if it wasn't already one, preserving context
    if not isinstance(error, PipelineError):
        raise PipelineError(f"Unexpected failure: {error_msg}", context=context or {}) from error
    else:
        raise error

# --- Main Entry Point for Standalone Testing ---

def main():
    """Test the logging infrastructure."""
    logger = get_logger()
    
    log_pipeline_start({"test_mode": True})
    
    try:
        logger.info("Simulating a data download...")
        # Simulate a specific error
        raise DataDownloadError("Failed to fetch dataset: 403 Forbidden", {"url": "https://example.com"})
    except PipelineError as e:
        handle_pipeline_error(e)
    except Exception as e:
        handle_pipeline_error(e)
    finally:
        log_pipeline_end("FAILED")

if __name__ == "__main__":
    main()