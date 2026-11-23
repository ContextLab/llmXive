"""
T034: Refactored Logging Configuration.

Centralizes logging setup to ensure consistent output formats across all
pipeline scripts (graph_builder, evaluator, retrieval_sim, etc.).
Replaces ad-hoc logging configurations in individual files.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Default log format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(
    name: str,
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    console: bool = True
) -> logging.Logger:
    """
    Sets up a logger with optional file and console handlers.
    Ensures handlers are not duplicated if the logger is re-initialized.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding handlers if they already exist
    if logger.handlers:
        return logger

    formatter = logging.Formatter(DEFAULT_FORMAT, datefmt=DEFAULT_DATE_FORMAT)

    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    if log_file:
        try:
            # Ensure directory exists
            log_file.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(str(log_file), mode='a')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except IOError as e:
            logger.error(f"Failed to create log file {log_file}: {e}")

    return logger

def get_pipeline_logger() -> logging.Logger:
    """
    Returns the standard logger for the pipeline.
    """
    return setup_logger("llmxive_pipeline", console=True)

def get_timing_logger() -> logging.Logger:
    """
    Returns a logger specifically for timing metrics.
    """
    return setup_logger("llmxive_timing", console=False)
