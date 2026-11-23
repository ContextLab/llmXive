"""
Standardized logging utilities for the antibiotic resistance pipeline.
Fixes circular import issue by avoiding 'logging' as a variable name conflicting with the module.
"""
import importlib
import sys
from pathlib import Path
from typing import Optional

# Import the real stdlib logging module under a different name to avoid shadowing
std_logging = importlib.import_module('logging')

# Define standard levels to avoid ambiguity
LOG_LEVELS = {
    "DEBUG": std_logging.DEBUG,
    "INFO": std_logging.INFO,
    "WARNING": std_logging.WARNING,
    "ERROR": std_logging.ERROR,
    "CRITICAL": std_logging.CRITICAL,
}

def get_logger(name: str, level: int = std_logging.INFO) -> std_logging.Logger:
    """
    Get or create a logger with the specified name and level.

    Args:
        name: Logger name (usually __name__)
        level: Logging level (e.g., std_logging.INFO)

    Returns:
        Configured logger instance
    """
    logger = std_logging.getLogger(name)

    # Avoid adding handlers multiple times if logger already exists
    if not logger.handlers:
        logger.setLevel(level)

        # Create console handler
        console_handler = std_logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # Create formatter
        formatter = std_logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(console_handler)

        # Prevent propagation to root logger to avoid duplicate logs
        logger.propagate = False

    return logger

def setup_file_logging(
    log_file: Path,
    level: int = std_logging.INFO,
    logger_name: Optional[str] = None
) -> std_logging.Logger:
    """
    Setup file logging for a specific logger.

    Args:
        log_file: Path to the log file
        level: Logging level
        logger_name: Name of the logger to configure (defaults to root)

    Returns:
        Configured logger
    """
    logger = std_logging.getLogger(logger_name) if logger_name else std_logging.getLogger()
    logger.setLevel(level)

    if not logger.handlers:
        # Create file handler
        file_handler = std_logging.FileHandler(log_file)
        file_handler.setLevel(level)

        # Create formatter
        formatter = std_logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)

        # Add handler
        logger.addHandler(file_handler)

    return logger

def init_pipeline_logging(log_dir: Path = Path("logs")) -> std_logging.Logger:
    """
    Initialize logging for the entire pipeline.
    Creates the log directory if it doesn't exist and sets up file logging.

    Args:
        log_dir: Directory to store log files

    Returns:
        Root logger configured for the pipeline
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "pipeline.log"

    # Setup file logging for root logger
    logger = setup_file_logging(log_file, level=std_logging.DEBUG)

    # Also setup console logging for immediate feedback
    console_handler = std_logging.StreamHandler(sys.stdout)
    console_handler.setLevel(std_logging.INFO)
    formatter = std_logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)

    # Clear existing handlers to avoid duplicates
    logger.handlers = []
    logger.addHandler(console_handler)

    return logger
