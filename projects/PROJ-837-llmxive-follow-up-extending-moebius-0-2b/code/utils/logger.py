"""
Logging infrastructure setup for llmXive pipeline.
Provides centralized logging configuration with support for CI and Research modes.
"""
import logging
import sys
import os
from pathlib import Path
from typing import Optional

# Global logger instance to avoid re-initialization
_project_logger: Optional[logging.Logger] = None

def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        name: Logger name (usually __name__ of the calling module)
        log_file: Optional path to log file. If None, only console output is used.
    
    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    
    # Avoid re-configuring if already configured
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Create formatter with timestamp, level, and message
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (always added)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        # Ensure parent directory exists
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    # Prevent propagation to root logger to avoid duplicate messages
    logger.propagate = False
    
    return logger

def setup_project_logger(log_dir: str = "data/logs") -> logging.Logger:
    """
    Initialize the main project logger with file output.
    This should be called once at the start of the application.
    
    Args:
        log_dir: Directory where log files will be stored.
    
    Returns:
        The configured project logger.
    """
    global _project_logger
    
    if _project_logger is not None:
        return _project_logger
    
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Generate log file name based on timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = str(log_path / f"pipeline_{timestamp}.log")
    
    _project_logger = get_logger("llmXive", log_file)
    _project_logger.info("Project logger initialized")
    
    return _project_logger

def get_console_only_logger(name: str) -> logging.Logger:
    """
    Get a logger that outputs only to console (no file).
    
    Args:
        name: Logger name.
    
    Returns:
        Console-only logger instance.
    """
    return get_logger(name, log_file=None)