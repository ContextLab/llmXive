import logging
import os
import sys
from pathlib import Path
from typing import Optional
from config.env_config import get_config, get_log_file_path, get_log_level

# Ensure the logs directory exists
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Global logger instance
_logger: Optional[logging.Logger] = None

def setup_logging(log_file: Optional[str] = None, level: Optional[str] = None) -> logging.Logger:
    """
    Configure the root logger to output to both a file and stdout.
    
    Args:
        log_file: Path to the log file. If None, uses the path from env config.
        level: Log level string (e.g., 'INFO', 'DEBUG'). If None, uses env config.
    
    Returns:
        The configured root logger.
    """
    global _logger
    
    # Resolve paths and levels
    if log_file is None:
        log_file = get_log_file_path()
    
    if level is None:
        level = get_log_level()
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Ensure the directory for the log file exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a custom logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Clear existing handlers to prevent duplicates on re-runs
    if logger.handlers:
        logger.handlers.clear()
    
    # Define formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File Handler
    try:
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # Fallback to stderr if file logging fails
        sys.stderr.write(f"Warning: Could not open log file {log_file}: {e}\n")
    
    # Console Handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    _logger = logger
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a logger. If setup_logging hasn't been called, it initializes it first.
    
    Args:
        name: Optional name for the logger (creates a child of the root logger).
    
    Returns:
        A configured logger instance.
    """
    global _logger
    if _logger is None:
        setup_logging()
    
    if name:
        return logging.getLogger(name)
    return _logger

def main():
    """
    Entry point for testing the logging configuration directly.
    """
    logger = setup_logging()
    logger.info("Logging infrastructure configured successfully.")
    logger.debug("Debug message test.")
    logger.warning("Warning message test.")
    logger.error("Error message test.")

if __name__ == "__main__":
    main()