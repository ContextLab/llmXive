import os
import sys
from pathlib import Path
from loguru import logger
from typing import Optional

# Remove default handler added by loguru
logger.remove()

def setup_logging(log_path: Optional[Path] = None, level: str = "INFO") -> None:
    """
    Initialize the logging infrastructure.
    
    Args:
        log_path: Path to the log file. If None, defaults to logs/pipeline.log
        level: Minimum logging level (DEBUG, INFO, WARNING, ERROR)
    """
    if log_path is None:
        log_path = Path("logs/pipeline.log")
    
    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove any existing handlers
    logger.remove()
    
    # Add file handler with detailed format
    logger.add(
        log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level=level,
        rotation="500 MB",
        retention="10 days",
        backtrace=True,
        diagnose=True,
    )
    
    # Add console handler for immediate feedback
    logger.add(
        sys.stderr,
        format="{time:HH:mm:ss} | {level: <8} | {message}",
        level=level,
    )

def get_logger() -> "loguru._logger.Logger":
    """
    Get the configured logger instance.
    
    Returns:
        The configured loguru logger
    """
    return logger
