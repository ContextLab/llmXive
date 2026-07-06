import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Constants for log paths
LOG_DIR = Path("code/state")
LOG_FILE = LOG_DIR / "pipeline.log"
ERROR_LOG_FILE = LOG_DIR / "errors.log"
MANIFEST_FILE = LOG_DIR / "manifest.json"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configuration constants
DEFAULT_LOG_LEVEL = logging.INFO
MAX_LOG_BYTES = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5

class LoggerConfig:
    """Configuration container for logging infrastructure."""
    def __init__(self, log_level: int = DEFAULT_LOG_LEVEL):
        self.log_level = log_level
        self.log_file = LOG_FILE
        self.error_log_file = ERROR_LOG_FILE
        self.manifest_file = MANIFEST_FILE
        self.max_bytes = MAX_LOG_BYTES
        self.backup_count = BACKUP_COUNT

def _get_formatter() -> logging.Formatter:
    """Create a standard log formatter with timestamp, level, and message."""
    return logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def _setup_console_handler(level: int) -> logging.StreamHandler:
    """Configure console logging handler."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(_get_formatter())
    return handler

def _setup_file_handler(log_path: Path, level: int) -> logging.handlers.RotatingFileHandler:
    """Configure rotating file logging handler."""
    # Ensure parent directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    handler = logging.handlers.RotatingFileHandler(
        str(log_path),
        maxBytes=MAX_LOG_BYTES,
        backupCount=BACKUP_COUNT
    )
    handler.setLevel(level)
    handler.setFormatter(_get_formatter())
    return handler

def initialize_logging(log_level: int = DEFAULT_LOG_LEVEL) -> logging.Logger:
    """
    Initialize the logging infrastructure for the project.
    
    Creates a root logger with:
    - Console output (INFO and above)
    - General log file (INFO and above)
    - Error-specific log file (ERROR and above)
    
    Args:
        log_level: Minimum logging level for general logs.
        
    Returns:
        The configured root logger instance.
    """
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Capture everything, handlers filter
    
    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create configuration
    config = LoggerConfig(log_level)
    
    # Add console handler
    console_handler = _setup_console_handler(config.log_level)
    logger.addHandler(console_handler)
    
    # Add general file handler
    file_handler = _setup_file_handler(config.log_file, config.log_level)
    logger.addHandler(file_handler)
    
    # Add error-specific file handler
    error_handler = _setup_file_handler(config.error_log_file, logging.ERROR)
    logger.addHandler(error_handler)
    
    # Log initialization
    logger.info("Logging infrastructure initialized successfully.")
    logger.debug(f"Log directory: {LOG_DIR.absolute()}")
    logger.debug(f"General log file: {config.log_file.absolute()}")
    logger.debug(f"Error log file: {config.error_log_file.absolute()}")
    
    return logger

def log_error_to_manifest(error_type: str, error_message: str, task_id: Optional[str] = None) -> None:
    """
    Log an error event to the state manifest.json file.
    
    This ensures critical errors are tracked alongside artifact checksums.
    
    Args:
        error_type: Category of error (e.g., 'DATA_MISSING', 'COMPUTATION_FAILED').
        error_message: Detailed description of the error.
        task_id: Optional ID of the task where the error occurred.
    """
    try:
        manifest_path = Path(MANIFEST_FILE)
        
        # Load existing manifest or create new one
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        else:
            manifest = {
                "artifacts": {},
                "errors": []
            }
        
        # Ensure errors list exists
        if "errors" not in manifest:
            manifest["errors"] = []
        
        # Create error entry
        error_entry = {
            "timestamp": logging.Formatter("%Y-%m-%d %H:%M:%S").format(logging.LogRecord("", 0, "", 0, "", (), None)),
            "type": error_type,
            "message": error_message,
            "task_id": task_id
        }
        
        manifest["errors"].append(error_entry)
        
        # Save updated manifest
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logging.error(f"Error recorded in manifest: {error_type} - {error_message}")
        
    except Exception as e:
        logging.critical(f"Failed to write error to manifest: {str(e)}")
        # Fallback to standard error log
        logging.error(f"Error details: {error_type} - {error_message}")

def log_data_missing_error(column_name: str, task_id: Optional[str] = None) -> None:
    """
    Helper to log the specific DATA_MISSING marker required by SC-005.
    
    Args:
        column_name: The name of the missing column.
        task_id: Optional task ID.
    """
    error_msg = f"DATA_MISSING: Required column {column_name} not found"
    logging.error(error_msg)
    log_error_to_manifest("DATA_MISSING", error_msg, task_id)

def log_variable_availability_success(predictors: list) -> None:
    """
    Helper to log the success marker for variable availability (SC-008).
    
    Args:
        predictors: List of predictor names found.
    """
    msg = f"Dataset variable availability is confirmed. Predictors found: {predictors}"
    logging.info(msg)

def log_variable_missing_error(predictor_name: str) -> None:
    """
    Helper to log the specific DATA_MISSING marker for missing predictors (SC-008).
    
    Args:
        predictor_name: The name of the missing predictor.
    """
    error_msg = f"DATA_MISSING: Predictor {predictor_name} not found"
    logging.error(error_msg)
    log_error_to_manifest("DATA_MISSING", error_msg, "Feature Engineering")

def main():
    """
    Entry point for logging initialization script.
    Demonstrates the logging infrastructure.
    """
    # Initialize logging
    logger = initialize_logging()
    
    logger.info("Starting logging infrastructure test.")
    
    # Test standard logging
    logger.debug("Debug message test.")
    logger.info("Info message test.")
    logger.warning("Warning message test.")
    logger.error("Error message test.")
    
    # Test custom error logging
    log_data_missing_error("test_column", "T012")
    log_variable_missing_error("test_predictor")
    
    logger.info("Logging infrastructure test completed.")
    logger.info(f"Check {LOG_FILE} and {ERROR_LOG_FILE} for output.")

if __name__ == "__main__":
    main()