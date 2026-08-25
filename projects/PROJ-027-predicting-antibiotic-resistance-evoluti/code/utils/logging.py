"""
Standardized logging utilities for the antibiotic resistance pipeline.
Fixes circular import issue by avoiding 'logging' as a variable name conflicting with the module.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

# Define standard levels to avoid ambiguity
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get or create a logger with the specified name and level.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (e.g., logging.INFO)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times if logger already exists
    if not logger.handlers:
        logger.setLevel(level)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(
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
    level: int = logging.INFO,
    logger_name: Optional[str] = None
) -> logging.Logger:
    """
    Setup file logging for a specific logger.
    
    Args:
        log_file: Path to the log file
        level: Logging level
        logger_name: Name of the logger to configure (defaults to root)
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(logger_name) if logger_name else logging.getLogger()
    logger.setLevel(level)
    
    if not logger.handlers:
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Add handler
        logger.addHandler(file_handler)
        
    return logger

def init_pipeline_logging(log_dir: Path = Path("logs")) -> logging.Logger:
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
    logger = setup_file_logging(log_file, level=logging.DEBUG)
    
    # Also setup console logging for immediate feedback
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers = []
    logger.addHandler(console_handler)
    
    return logger
