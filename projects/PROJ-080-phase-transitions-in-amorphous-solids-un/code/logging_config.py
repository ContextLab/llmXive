import logging
import os
from pathlib import Path
from typing import Optional
import sys

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

def configure_logging(level: int = logging.INFO) -> None:
    """Configures the root logger."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOG_DIR / "pipeline.log")
        ]
    )

def get_logger(name: str) -> logging.Logger:
    """Gets a logger with the specified name."""
    return logging.getLogger(name)

def log_indeterminate_warning(message: str) -> None:
    """Logs a warning for indeterminate trajectories."""
    logger = get_logger(__name__)
    logger.warning(f"INDETERMINATE: {message}")

def log_multi_yield_event(message: str) -> None:
    """Logs a warning for multiple yield events (should not happen per FR-002)."""
    logger = get_logger(__name__)
    logger.warning(f"MULTI-YIELD: {message}")

def log_data_fetch_failure(message: str) -> None:
    """Logs an error for data fetch failures."""
    logger = get_logger(__name__)
    logger.error(f"FETCH FAILURE: {message}")