import logging
import os
from pathlib import Path
from typing import Optional
import sys

def configure_logging(log_level: int = logging.INFO) -> None:
    """Configure logging infrastructure."""
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Clear existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler for warnings
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "pipeline.log")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def get_logger(name: str = "preprocess") -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)

def log_indeterminate_warning(message: str) -> None:
    """Log warning for indeterminate trajectories."""
    logger = get_logger()
    logger.warning(f"INDETERMINATE: {message}")

def log_multi_yield_event(event_details: Dict) -> None:
    """Log detailed metrics for multi-yield events."""
    logger = get_logger()
    logger.warning(f"MULTI-YIELD: {event_details}")

def log_data_fetch_failure(error_message: str) -> None:
    """Log failure when real data fetch fails."""
    logger = get_logger()
    logger.error(f"DATA_FETCH_FAILURE: {error_message}")
