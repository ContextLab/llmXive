"""
Logging configuration utilities.

Refactored to ensure consistent logging setup across the project.
"""
import logging
import os
from pathlib import Path

# Default log file path relative to project root
DEFAULT_LOG_FILE = "data/ingest.log"

def setup_logging(log_file: str = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configure the root logger with a file handler.
    
    Args:
        log_file: Path to the log file. Defaults to 'data/ingest.log'.
        level: Logging level. Defaults to INFO.
        
    Returns:
        The configured logger instance.
    """
    if log_file is None:
        log_file = DEFAULT_LOG_FILE
        
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure basic logging
    logging.basicConfig(
        filename=str(log_path),
        level=level,
        format='%(asctime)s %(levelname)s %(name)s %(message)s',
        force=True  # Force reconfiguration if already configured
    )
    
    # Also log to console for immediate feedback
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))
    logging.getLogger('').addHandler(console)
    
    return logging.getLogger(__name__)

def test_log_entry(logger: logging.Logger = None) -> bool:
    """
    Emits a test log entry to verify logging is working.
    
    Args:
        logger: Optional logger instance. If None, uses the root logger.
        
    Returns:
        True if the log entry was successfully written.
    """
    if logger is None:
        logger = logging.getLogger()
        
    logger.info("Logging configuration test entry.")
    
    # Verify file exists
    log_path = Path(DEFAULT_LOG_FILE)
    return log_path.exists()
