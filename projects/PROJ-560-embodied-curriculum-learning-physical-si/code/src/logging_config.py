import logging
import os
import sys
from pathlib import Path
from typing import Optional

def setup_logging(
    log_level: Optional[int] = None,
    log_file: Optional[str] = None,
    project_root: Optional[Path] = None
) -> logging.Logger:
    """
    Configure and return the project logger with both console and file handlers.
    
    Args:
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO). Defaults to INFO.
        log_file: Optional path to a log file. If None, only console output is used.
        project_root: Base path for relative log file paths. Defaults to current working directory.
    
    Returns:
        A configured logger instance.
    """
    if log_level is None:
        log_level = logging.INFO
    
    logger = logging.getLogger("embodied_curriculum")
    logger.setLevel(log_level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler (if specified)
    if log_file:
        if project_root:
            log_path = project_root / log_file
        else:
            log_path = Path(log_file)
        
        # Ensure directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_path, mode='a')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
