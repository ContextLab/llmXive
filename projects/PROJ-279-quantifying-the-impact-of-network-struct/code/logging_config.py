import logging
import os
import sys
from pathlib import Path
from typing import Optional
from config.env_config import get_config, get_log_file_path, get_log_level

_logger_instance: Optional[logging.Logger] = None

def setup_logging():
    """
    Configure logging infrastructure to output to both file and stdout.
    Logs are written to logs/analysis.log as per project spec.
    """
    global _logger_instance
    
    if _logger_instance is not None:
        return _logger_instance

    log_file = get_log_file_path()
    log_level = get_log_level()
    
    # Ensure log directory exists
    log_dir = Path(log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Avoid adding handlers multiple times if called repeatedly
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    _logger_instance = root_logger
    return _logger_instance

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance, ensuring logging is configured first.
    
    Args:
        name: Name for the logger. If None, returns root logger.
    
    Returns:
        Configured logger instance
    """
    setup_logging()
    if name:
        return logging.getLogger(name)
    return logging.getLogger()

def main():
    """
    Test logging configuration.
    """
    logger = setup_logging()
    logger.info("Logging configuration test successful.")
    logger.debug("Debug message test.")
    logger.warning("Warning message test.")

if __name__ == "__main__":
    main()
