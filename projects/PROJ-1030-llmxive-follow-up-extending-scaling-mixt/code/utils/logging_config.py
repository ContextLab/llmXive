import logging
import os
import sys
from pathlib import Path
from typing import Optional
import traceback

# Ensure logs directory exists
LOGS_DIR = Path("code/../logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / "pipeline.log")
    ]
)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Module name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

def fail_loudly(
    logger: logging.Logger, 
    message: str, 
    exception: Optional[Exception] = None,
    error_code: int = 1
) -> None:
    """
    Log a critical error and exit immediately.
    
    This is the "FAIL LOUDLY" mechanism. It ensures that:
    1. The error is logged with full traceback if available
    2. The process exits with a non-zero code
    3. No synthetic fallback or silent failure occurs
    
    Args:
        logger: Logger instance to use
        message: Human-readable error message
        exception: Optional exception instance to extract traceback from
        error_code: Exit code to use (default 1)
    """
    error_msg = f"FATAL ERROR: {message}"
    
    if exception:
        error_msg += f"\nException Type: {type(exception).__name__}"
        error_msg += f"\nException Message: {str(exception)}"
        error_msg += f"\nTraceback:\n{''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))}"
    
    logger.critical(error_msg)
    
    # Flush logs before exit
    for handler in logger.handlers:
        handler.flush()
    
    sys.exit(error_code)

def configure_data_fetch_logger(name: str = "data_fetch") -> logging.Logger:
    """
    Configure a specialized logger for data fetching operations.
    
    This logger:
    - Logs to a separate file for audit purposes
    - Uses higher verbosity for retry attempts
    - Ensures "FAIL LOUDLY" on unrecoverable fetch errors
    
    Args:
        name: Logger name (default: "data_fetch")
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # File handler for data fetch logs
    file_handler = logging.FileHandler(LOGS_DIR / "data_fetch.log")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler for critical errors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
