"""
Logging infrastructure setup.
"""
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(log_level: str = "INFO", log_dir: Path = None) -> logging.Logger:
    """
    Configure logging for the project.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
    
    Returns:
        Configured logger instance
    """
    # Create log directory if needed
    if log_dir is None:
        log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    log_file = log_dir / f"cmb_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, log_level))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, log_level))
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (module name if not specified)
    
    Returns:
        Logger instance
    """
    if name is None:
        name = __name__
    return logging.getLogger(name)

def main():
    """Test logging setup."""
    logger = setup_logging()
    logger.info("Logging infrastructure initialized")
    logger.debug("Debug message")
    logger.warning("Warning message")
    logger.error("Error message")

if __name__ == "__main__":
    main()