"""
Centralised logging utilities for the project.

The pipeline uses three logical loggers:
* ``data_quality`` – records high‑level pipeline status and validation messages.
* ``exclusion``    – records records that are filtered out with reasons.
* ``pipeline``    – general informational logger for each script.

All loggers write to ``stdout`` and also to a file under
``results/logs/``.  The helpers below ensure that duplicate handlers are not
added when modules import this file multiple times.
"""

import logging
import sys
from pathlib import Path

from config import RESULTS_LOG_DIR

# ----------------------------------------------------------------------
# Helper to create a logger with a file handler (if not already present)
# ----------------------------------------------------------------------
def _get_logger(name: str, log_file: Path) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers on repeated imports
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        # Console handler
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(formatter)
        logger.addHandler(console)

        # File handler
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# ----------------------------------------------------------------------
# Public logger factories
# ----------------------------------------------------------------------
def get_data_quality_logger() -> logging.Logger:
    """
    Logger for data‑quality / validation messages.
    Writes to ``results/logs/data_quality.log``.
    """
    log_path = RESULTS_LOG_DIR / "data_quality.log"
    return _get_logger("data_quality", log_path)

def get_exclusion_logger() -> logging.Logger:
    """
    Logger for records that are excluded during filtering.
    Writes to ``results/logs/exclusion.log``.
    """
    log_path = RESULTS_LOG_DIR / "exclusion.log"
    return _get_logger("exclusion", log_path)

def setup_logging() -> None:
    """
    Initialise a generic ``pipeline`` logger used by many scripts.
    The logger writes to ``results/logs/pipeline.log`` and stdout.
    """
    _ = _get_logger("pipeline", RESULTS_LOG_DIR / "pipeline.log")
