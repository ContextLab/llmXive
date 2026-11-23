import logging
import sys
import os
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
import logging.handlers

# Custom Exception Classes
class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DataDownloadError(PipelineError):
    """Raised when data download fails."""
    pass

class DataIngestionError(PipelineError):
    """Raised when data ingestion fails."""
    pass

class FeatureEngineeringError(PipelineError):
    """Raised when feature engineering fails."""
    pass

class ModelTrainingError(PipelineError):
    """Raised when model training fails."""
    pass

class ScreeningError(PipelineError):
    """Raised when screening process fails."""
    pass

class ConfigurationError(PipelineError):
    """Raised when configuration is invalid."""
    pass

# Global logger registry to prevent duplicate handlers
_loggers = {}

# Configuration constants for log rotation
LOG_DIR = Path("logs")
LOG_FILE = "pipeline.log"
MAX_BYTES = 10 * 1024 * 1024  # 10 MB per file
BACKUP_COUNT = 5  # Keep 5 rotated files
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def _ensure_log_dir():
    """Ensure the logs directory exists."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with rotation configured.
    Returns a singleton logger per name to avoid duplicate handlers.
    """
    if name in _loggers:
        return _loggers[name]

    _ensure_log_dir()
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Avoid adding handlers if already present (e.g., in tests or re-runs)
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(console_handler)

        # File handler with rotation (RotatingFileHandler)
        log_path = LOG_DIR / LOG_FILE
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(file_handler)

        # Prevent propagation to root logger to avoid double logging
        logger.propagate = False

    _loggers[name] = logger
    return logger

def log_info(msg: str, name: str = "pipeline") -> None:
    """Log an info message."""
    get_logger(name).info(msg)

def log_warning(msg: str, name: str = "pipeline") -> None:
    """Log a warning message."""
    get_logger(name).warning(msg)

def log_error(msg: str, name: str = "pipeline") -> None:
    """Log an error message."""
    get_logger(name).error(msg)

def log_critical(msg: str, name: str = "pipeline") -> None:
    """Log a critical message."""
    get_logger(name).critical(msg)

def log_debug(msg: str, name: str = "pipeline") -> None:
    """Log a debug message."""
    get_logger(name).debug(msg)

def log_pipeline_start(config_summary: Optional[dict] = None) -> None:
    """Log the start of the pipeline execution."""
    logger = get_logger("pipeline")
    logger.info("=" * 60)
    logger.info("PIPELINE STARTED")
    logger.info(f"Timestamp: {datetime.now().strftime(DATE_FORMAT)}")
    if config_summary:
        logger.info(f"Configuration: {config_summary}")
    logger.info("=" * 60)

def log_pipeline_end(success: bool, duration_seconds: Optional[float] = None) -> None:
    """Log the end of the pipeline execution."""
    logger = get_logger("pipeline")
    logger.info("=" * 60)
    if success:
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
    else:
        logger.error("PIPELINE FAILED")
    if duration_seconds:
        logger.info(f"Duration: {duration_seconds:.2f} seconds")
    logger.info("=" * 60)

def handle_pipeline_error(error: Exception, name: str = "pipeline") -> None:
    """
    Centralized error handler for pipeline failures.
    Logs the error details and stack trace.
    """
    logger = get_logger(name)
    logger.critical(f"Unhandled pipeline error: {type(error).__name__}: {str(error)}")
    # Re-raise to allow the caller to handle exit codes if needed
    raise error

def main():
    """
    Demo function to test logger initialization and rotation configuration.
    Generates enough log entries to demonstrate the logger is working.
    """
    logger = get_logger("test_rotation")
    log_pipeline_start({"test_mode": True})
    
    logger.info("Testing log rotation configuration...")
    logger.info(f"Max log file size: {MAX_BYTES / (1024*1024)} MB")
    logger.info(f"Backup count: {BACKUP_COUNT}")
    
    # Log a series of messages to ensure the file handler is active
    for i in range(10):
        logger.info(f"Test log message {i+1}")
    
    log_pipeline_end(True)
    print("Logger initialized successfully with rotation.")

if __name__ == "__main__":
    main()