import logging
import os
import sys
from pathlib import Path
from typing import Optional, Union

# Global flag to prevent duplicate handler configuration
_logging_configured = False

def get_project_root() -> Path:
    """Return the root directory of the project."""
    return Path(__file__).parent.parent.parent

def validate_log_directory() -> Path:
    """Ensure the logs directory exists and is writable. Returns the path."""
    root = get_project_root()
    log_dir = root / "logs"
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)
    if not os.access(log_dir, os.W_OK):
        raise PermissionError(f"Log directory {log_dir} is not writable.")
    return log_dir

def setup_logger(name: str, log_file: Optional[str] = None, level=logging.INFO) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Ensures log directory exists.
    Prevents duplicate handlers on repeated calls.
    Sets level on the logger and handlers.
    """
    global _logging_configured
    
    # Ensure log directory exists before attempting file operations
    try:
        log_dir_path = validate_log_directory()
    except PermissionError as e:
        # Fallback to stdout if log dir is inaccessible
        logging.basicConfig(level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        return logging.getLogger(name)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent adding duplicate handlers if already configured
    if logger.handlers:
        # If handlers exist, ensure they match expected level/format if possible, 
        # but primarily just return existing configured logger to avoid duplication
        return logger

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler (optional)
    if log_file:
        # Resolve relative to logs dir if not absolute
        if not os.path.isabs(log_file):
            log_file_path = log_dir_path / log_file
        else:
            log_file_path = Path(log_file)
        
        # Ensure parent directory exists
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            fh = logging.FileHandler(log_file_path)
            fh.setLevel(level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except (IOError, PermissionError) as e:
            logger.warning(f"Could not open log file {log_file_path}: {e}. Logging to console only.")

    logger.propagate = False
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance. 
    If not configured yet, performs default setup.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Default to a file logger in logs/app.log if no specific config provided yet
        # This ensures immediate usability without explicit setup calls
        return setup_logger(name, log_file="app.log")
    return logger

def log_exception(e: Exception, logger_name: str = "exception") -> None:
    """
    Log an exception with full traceback info.
    
    Args:
        e: The exception instance.
        logger_name: Name of the logger to use.
    """
    logger = get_logger(logger_name)
    logger.error("An exception occurred", exc_info=True, extra={"exception": str(e)})

def install_global_exception_handler() -> None:
    """
    Install a global exception handler to catch unhandled exceptions
    and log them before the program crashes.
    """
    def global_handler(exctype, value, traceback):
        logger = get_logger("unhandled_exception")
        logger.critical(f"Unhandled exception of type {exctype.__name__}: {value}", exc_info=(exctype, value, traceback))
        # Print to stderr as well for immediate visibility
        print(f"Critical unhandled error: {value}", file=sys.stderr)
    
    sys.excepthook = global_handler

def main():
    """
    Entry point for testing the logger module directly.
    Demonstrates configuration, logging, and exception handling.
    """
    print("Initializing logger infrastructure...")
    
    # 1. Validate directory
    try:
        log_dir = validate_log_directory()
        print(f"Log directory validated: {log_dir}")
    except PermissionError as e:
        print(f"Log directory validation failed: {e}")
        return

    # 2. Install global handler
    install_global_exception_handler()
    
    # 3. Get a logger and log a test message
    logger = get_logger("test_logger")
    logger.info("Logger infrastructure configured successfully.")
    
    # 4. Test exception logging
    try:
        raise ValueError("Test exception for logging")
    except Exception as e:
        log_exception(e)
    
    print("Logger test complete. Check 'logs/app.log' for output.")

if __name__ == "__main__":
    main()