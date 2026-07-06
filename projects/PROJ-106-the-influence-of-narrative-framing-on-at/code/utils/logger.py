import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# Configure logging directory
LOG_DIR = Path('data/logs')
LOG_DIR.mkdir(parents=True, exist_ok=True)

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with file and console handlers.
    
    Args:
        name: Logger name
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    log_file = LOG_DIR / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get an existing logger or create a new one."""
    return logging.getLogger(name)

def log_audit_event(logger: logging.Logger, event_type: str, details: Dict[str, Any]) -> None:
    """Log an audit event."""
    logger.info(f"AUDIT [{event_type}]: {details}")

def log_script_start(logger: logging.Logger, script_name: str) -> None:
    """Log the start of a script execution."""
    logger.info(f"SCRIPT_START: {script_name}")

def log_script_end(logger: logging.Logger, script_name: str, success: bool) -> None:
    """Log the end of a script execution."""
    status = "SUCCESS" if success else "FAILURE"
    logger.info(f"SCRIPT_END: {script_name} [{status}]")

def log_data_operation(logger: logging.Logger, operation: str, count: Optional[int] = None) -> None:
    """Log a data operation."""
    if count is not None:
        logger.info(f"DATA_OP: {operation} (count={count})")
    else:
        logger.info(f"DATA_OP: {operation}")

def log_analysis_step(logger: logging.Logger, step_name: str, result: Dict[str, Any]) -> None:
    """Log an analysis step."""
    logger.info(f"ANALYSIS_STEP: {step_name} -> {result}")

# Convenience functions for direct logging
def info(msg: str) -> None:
    """Log an info message."""
    logging.info(msg)

def debug(msg: str) -> None:
    """Log a debug message."""
    logging.debug(msg)

def warning(msg: str) -> None:
    """Log a warning message."""
    logging.warning(msg)

def error(msg: str) -> None:
    """Log an error message."""
    logging.error(msg)

def critical(msg: str) -> None:
    """Log a critical message."""
    logging.critical(msg)

def exception(msg: str) -> None:
    """Log an exception message."""
    logging.exception(msg)

def log_exception(logger: logging.Logger, exc: Exception) -> None:
    """Log an exception with traceback."""
    logger.exception(f"EXCEPTION: {exc}")
