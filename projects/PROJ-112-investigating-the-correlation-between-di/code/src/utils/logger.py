import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Configuration constants
LOG_DIR = Path("data/logs")
LOG_FILE = "pipeline.log"
R_LOG_FILE = "r_output.log"

# Cache for loggers to ensure single instance per name
_loggers: dict = {}

def get_logger(name: str, log_level: int = logging.INFO) -> logging.Logger:
    """
    Retrieve or create a logger with the given name.
    
    Configures:
    - A file handler for general pipeline logs.
    - A specific file handler for R/MaAsLin2 output if the name indicates R usage.
    - Console handler for immediate feedback.
    
    Args:
        name: Logger name (e.g., 'maaslin2', 'ingestion', 'preprocessing').
        log_level: Minimum log level to capture.
        
    Returns:
        Configured logging.Logger instance.
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Prevent duplicate handlers if called multiple times in same session
    if logger.handlers:
        _loggers[name] = logger
        return logger
    
    # Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # General formatter for pipeline logs
    general_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # File handler for general logs
    file_handler = logging.FileHandler(LOG_DIR / LOG_FILE)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(general_formatter)
    logger.addHandler(file_handler)
    
    # Console handler for immediate visibility
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(general_formatter)
    logger.addHandler(console_handler)
    
    # Specialized handler for R/MaAsLin2 output
    # Detect if this logger is intended for R output based on name
    if 'r' in name.lower() or 'maaslin' in name.lower() or 'r_package' in name.lower():
        r_formatter = logging.Formatter(
            '[R-OUTPUT] %(asctime)s - %(levelname)s - %(message)s'
        )
        r_handler = logging.FileHandler(LOG_DIR / R_LOG_FILE)
        r_handler.setLevel(logging.DEBUG)  # Capture all R output
        r_handler.setFormatter(r_formatter)
        logger.addHandler(r_handler)
        
        # Also capture convergence warnings specifically
        warning_formatter = logging.Formatter(
            '[R-WARNING] %(asctime)s - %(message)s'
        )
        warning_handler = logging.FileHandler(LOG_DIR / "r_warnings.log")
        warning_handler.setLevel(logging.WARNING)
        warning_handler.setFormatter(warning_formatter)
        logger.addHandler(warning_handler)
    
    _loggers[name] = logger
    return logger

def reset_loggers() -> None:
    """
    Reset all cached loggers. Useful for testing or reconfiguration.
    """
    for name in list(_loggers.keys()):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.setLevel(logging.NOTSET)
        del _loggers[name]
