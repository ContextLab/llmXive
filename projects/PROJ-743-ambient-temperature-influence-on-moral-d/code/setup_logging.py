"""
setup_logging.py
-----------------
Central logging utilities for the project. Provides two loggers:
* data_quality_logger: logs high‑level pipeline messages to the console and
  to ``results/logs/data_quality.log``.
* exclusion_logger: logs records that are filtered out during ingestion to
  ``results/logs/exclusion_log.csv`` (as a CSV) and also emits brief messages
  to the console.

The loggers are lightweight and avoid duplicate handlers when imported
multiple times.
"""
import logging
import sys
from pathlib import Path

from config import RESULTS_LOG_DIR

# Ensure the results/logs directory exists (config already creates it,
# but this is defensive in case the module is imported before config runs)
(RESULTS_LOG_DIR).mkdir(parents=True, exist_ok=True)


def _get_logger(name: str, log_file: Path | None = None) -> logging.Logger:
    """Create or retrieve a logger with a sensible formatter."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers if this function is called repeatedly.
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Console handler (always present)
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # Optional file handler
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    return logger


def get_data_quality_logger() -> logging.Logger:
    """
    Logger for high‑level pipeline status messages.
    Writes to ``results/logs/data_quality.log``.
    """
    log_path = RESULTS_LOG_DIR / "data_quality.log"
    return _get_logger("data_quality", log_path)


def get_exclusion_logger() -> logging.Logger:
    """
    Logger used during ingestion to note why records are excluded.
    The logger itself only emits to the console; the actual CSV logging
    is performed directly in ``code/ingestion.py`` when records are
    written to ``results/logs/exclusion_log.csv``.
    """
    return _get_logger("exclusion")
