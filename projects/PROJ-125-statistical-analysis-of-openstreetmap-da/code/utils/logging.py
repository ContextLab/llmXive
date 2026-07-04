"""
Logging infrastructure setup.
"""
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
from config import get_path

def setup_logging(
    name: str = "llmXive",
    log_file: Optional[Path] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Setup logging with file and stdout handlers.
    
    Args:
        name: Logger name
        log_file: Optional path to log file
        level: Logging level
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File Handler (if requested)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    
    return logger

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get an existing logger or create one with default settings.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logging(name)
    return logger

def log_module_imports(logger: logging.Logger, module_name: str) -> None:
    """
    Log that a module has been imported.
    """
    logger.info(f"Module imported: {module_name}")

def log_error_context(
    logger: logging.Logger,
    error: Exception,
    context: Optional[str] = None
) -> None:
    """
    Log an error with context.
    """
    msg = f"Error: {str(error)}"
    if context:
        msg = f"{context} - {msg}"
    logger.error(msg, exc_info=True)