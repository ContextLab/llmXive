import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from config import ensure_dirs

# Global logger instance to be used across the project
_logger_instance = None

class ColorFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def format(self, record):
        # Apply color to the level name
        levelname = record.levelname
        color = self.COLORS.get(levelname, self.COLORS['RESET'])
        record.levelname = f"{color}{levelname}{self.COLORS['RESET']}"
        
        # Format the message
        formatted_message = super().format(record)
        return formatted_message

def setup_logging(log_level: str = "INFO", log_file: str = "pipeline.log") -> logging.Logger:
    """
    Configure the root logger with both console and file handlers.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Name of the log file (stored in logs/)
    
    Returns:
        Configured logger instance
    """
    global _logger_instance
    
    if _logger_instance is not None:
        return _logger_instance

    # Ensure logs directory exists
    ensure_dirs()
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    log_path = logs_dir / log_file

    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers to avoid duplicates in interactive environments
    if logger.handlers:
        logger.handlers.clear()

    # Create formatter for file (no colors)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Create rotating file handler (max 10MB, 5 backup files)
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_handler.setFormatter(file_formatter)

    # Create formatter for console (with colors)
    console_formatter = ColorFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Store instance
    _logger_instance = logger
    
    logger.info(f"Logging initialized. File: {log_path}")
    return logger

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get a named logger instance.
    
    Args:
        name: Logger name (usually __name__ of the module)
    
    Returns:
        Logger instance
    """
    # Ensure root logger is set up
    if _logger_instance is None:
        setup_logging()
    
    return logging.getLogger(name)

def log_exception(exc: Exception, context: str = "") -> None:
    """
    Log an exception with full traceback.
    
    Args:
        exc: The exception instance
        context: Optional context string describing where the error occurred
    """
    logger = get_logger()
    error_msg = f"{context}: {str(exc)}" if context else str(exc)
    logger.exception(error_msg)

def handle_critical_error(exc: Exception, exit_code: int = 1) -> None:
    """
    Log a critical error and exit the program.
    
    Args:
        exc: The exception instance
        exit_code: Exit code for the process
    """
    logger = get_logger()
    logger.critical(f"FATAL ERROR: {str(exc)}")
    log_exception(exc, "Critical failure")
    sys.exit(exit_code)
