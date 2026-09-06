import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from config import ensure_dirs

# Global logger instance cache to ensure consistent configuration across the project
_logger_instance = None
_setup_called = False

class ColorFormatter(logging.Formatter):
    """
    Custom formatter that adds color to log levels for console output.
    Helps developers quickly identify error severity in the terminal.
    """
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)

def setup_logging(
    log_file: str = "logs/pipeline.log",
    level: int = logging.INFO,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG
) -> None:
    """
    Configures the global logging infrastructure for the project.
    
    This function:
    1. Ensures the log directory exists.
    2. Creates a RotatingFileHandler for persistent logs.
    3. Creates a StreamHandler for console output with colors.
    4. Configures the root logger to capture all library logs (statsmodels, pandas, etc.).
    
    Args:
        log_file: Relative path to the log file from project root.
        level: Global root logger level.
        console_level: Minimum level for console output.
        file_level: Minimum level for file output.
    """
    global _setup_called
    
    if _setup_called:
        return

    # Ensure logs directory exists
    log_path = Path(log_file)
    ensure_dirs(log_path.parent)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to prevent duplicates on re-runs in same session
    if root_logger.handlers:
        root_logger.handlers.clear()

    # File Handler (Rotating to prevent infinite growth)
    # Max size 10MB, keep 5 backups
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(file_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_formatter = ColorFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Log startup info
    root_logger.info(f"Logging initialized. File: {log_path.absolute()}")
    _setup_called = True

def get_logger(name: str = "project") -> logging.Logger:
    """
    Retrieves a logger instance with the specified name.
    
    If setup_logging() has not been called yet, this function will
    call it with default settings to ensure a logger is always available.
    
    Args:
        name: Name of the logger (usually __name__ of the calling module).
    
    Returns:
        A configured logging.Logger instance.
    """
    global _setup_called
    if not _setup_called:
        setup_logging()
    
    return logging.getLogger(name)

# Convenience function to handle common error patterns
def log_exception(logger: logging.Logger, msg: str, exc_info: bool = True) -> None:
    """
    Logs an exception with full traceback.
    
    Args:
        logger: The logger instance to use.
        msg: The message to log.
        exc_info: Whether to include exception info (default True).
    """
    logger.error(msg, exc_info=exc_info)

def handle_critical_error(logger: logging.Logger, msg: str, exit_code: int = 1) -> None:
    """
    Logs a critical error and exits the program.
    
    Args:
        logger: The logger instance to use.
        msg: The error message.
        exit_code: The exit code to return.
    """
    logger.critical(msg)
    sys.exit(exit_code)
