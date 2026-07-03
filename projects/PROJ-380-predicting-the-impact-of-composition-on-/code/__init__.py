"""
llmXive Research Pipeline: Predicting the Impact of Composition on Shear Modulus of BMGs.

This package provides the core logic for data ingestion, feature engineering,
model training, and evaluation for Bulk Metallic Glass (BMG) research.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Configure package-wide logging
def setup_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configure logging for the research pipeline.

    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_file: Optional path to a log file. If None, logs only to console.

    Returns:
        The root logger for the package.
    """
    logger = logging.getLogger("llmXive_bmg")
    logger.setLevel(log_level)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# Initialize default logger configuration
logger = setup_logging()

__all__ = ["setup_logging", "logger"]
