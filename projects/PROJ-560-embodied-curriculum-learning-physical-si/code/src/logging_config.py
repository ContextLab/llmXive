"""
Logging configuration module.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional

def setup_logging(log_level: int = logging.INFO) -> None:
    """
    Configure the root logger.

    Args:
        log_level (int): Logging level (e.g., logging.INFO, logging.DEBUG).
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("data/derivation_logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "pipeline.log"

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logger = logging.getLogger(__name__)
    logger.info("Logging configuration initialized.")
