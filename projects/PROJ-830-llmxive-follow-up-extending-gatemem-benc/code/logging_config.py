"""
Logging configuration for the GateMem Gatekeeper project.

Provides:
- Centralized logging setup with file and console handlers.
- Error handling wrappers for common operations.
- Random seed pinning for reproducibility.
- Verification of log file creation.
"""
import os
import sys
import logging
import random
from typing import Optional, Any
from datetime import datetime
import numpy as np
import torch

# Project-specific paths
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "logs")
LOG_FILE_NAME = "gatekeeper.log"
DEFAULT_LOG_LEVEL = logging.INFO

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)


def setup_logging(
    log_file_name: str = LOG_FILE_NAME,
    log_level: int = DEFAULT_LOG_LEVEL,
    log_dir: str = LOG_DIR
) -> logging.Logger:
    """
    Configure and return the project logger.
    
    Sets up:
    - A file handler writing to `log_dir/log_file_name`.
    - A console handler for immediate feedback.
    - A specific formatter with timestamp, level, and message.
    
    Args:
        log_file_name: Name of the log file.
        log_level: Logging level (e.g., logging.INFO, logging.DEBUG).
        log_dir: Directory to store log files.
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    # Ensure directory exists
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file_name)

    # Create logger
    logger = logging.getLogger("gatekeeper_logger")
    logger.setLevel(log_level)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File Handler
    try:
        fh = logging.FileHandler(log_path, mode='a', encoding='utf-8')
        fh.setLevel(log_level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except IOError as e:
        # Fallback to console only if file creation fails
        print(f"Warning: Could not create log file {log_path}: {e}", file=sys.stderr)

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    logger.info(f"Logging initialized. Output file: {log_path}")
    return logger


def pin_random_seed(seed: int = 42) -> None:
    """
    Pin random seeds for reproducibility across libraries.
    
    Sets seeds for:
    - Python's built-in random module
    - NumPy
    - PyTorch (CPU and CUDA if available)
    - Environment variable for some ops (if supported)
    
    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    
    # Deterministic behavior for some ops (optional, may impact performance)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    
    os.environ['PYTHONHASHSEED'] = str(seed)


class ErrorHandling:
    """
    Utility class for wrapping operations with logging and error handling.
    """
    
    @staticmethod
    def log_and_raise(logger: logging.Logger, exception: Exception, msg: str = "An error occurred") -> None:
        """
        Log an error message and re-raise the exception.
        
        Args:
            logger: The logger instance to use.
            exception: The exception to log and raise.
            msg: Custom error message prefix.
        """
        logger.error(f"{msg}: {str(exception)}", exc_info=True)
        raise exception
    
    @staticmethod
    def try_execute(
        func: Any, 
        logger: logging.Logger, 
        default_return: Optional[Any] = None, 
        error_msg: str = "Execution failed"
    ) -> Any:
        """
        Execute a function with error handling, logging the error and returning a default.
        
        Args:
            func: The callable to execute.
            logger: The logger instance.
            default_return: Value to return if an exception occurs.
            error_msg: Message to log on failure.
            
        Returns:
            Result of func or default_return.
        """
        try:
            return func()
        except Exception as e:
            logger.error(f"{error_msg}: {str(e)}", exc_info=True)
            return default_return


def verify_log_creation(log_path: str) -> bool:
    """
    Verify that the log file exists and has content.
    
    Args:
        log_path: Path to the log file.
        
    Returns:
        bool: True if file exists and is not empty, False otherwise.
    """
    if not os.path.exists(log_path):
        return False
    if os.path.getsize(log_path) == 0:
        return False
    return True


# Initialize logger for module-level use
# Note: In a real pipeline, this might be called explicitly in the main entry point
# to ensure the log file path is correct relative to the execution context.
logger = setup_logging()


if __name__ == "__main__":
    """
    Verification script to ensure logging configuration works and creates the log file.
    """
    import time
    
    # Pin seed for this run
    pin_random_seed(42)
    
    # Log startup
    logger.info("Starting logging configuration verification.")
    
    # Simulate some work
    logger.debug("Debug message test.")
    logger.warning("Warning message test.")
    logger.error("Error message test (simulated).")
    
    # Verify file creation
    log_path = os.path.join(LOG_DIR, LOG_FILE_NAME)
    time.sleep(0.1) # Ensure file write completes
    
    if verify_log_creation(log_path):
        logger.info("SUCCESS: Log file created and verified.")
    else:
        logger.error("FAILURE: Log file verification failed.")
        sys.exit(1)