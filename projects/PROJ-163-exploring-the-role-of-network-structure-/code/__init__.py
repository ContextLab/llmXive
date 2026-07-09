"""
llmXive Project: Exploring the Role of Network Structure in Superconducting Qubit Coupling
"""
__version__ = "0.1.0"

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

# Ensure logs directory exists
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "llmXive.log"

def setup_logger(
    name: str = "llmXive",
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    console: bool = True
) -> logging.Logger:
    """
    Configure and return a logger with file and optional console handlers.
    
    Args:
        name: Logger name.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Path to log file. Defaults to logs/llmXive.log.
        console: Whether to add a console handler.
    
    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # File handler with rotation
    file_handler_path = log_file or LOG_FILE
    try:
        file_handler = RotatingFileHandler(
            file_handler_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # Fallback to stderr if file logging fails
        sys.stderr.write(f"Warning: Could not open log file {file_handler_path}: {e}\n")
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

# Initialize default logger for the package
logger = setup_logger()
