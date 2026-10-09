"""
utils/logger.py
----------------
Centralized logger for the neural entropy pipeline.

This module provides a simple, file‑based logger that writes all
pipeline‑wide messages to ``logs/pipeline.log``.  It is deliberately
lightweight and has no external dependencies beyond the Python
standard library, making it safe to import from any stage script.

Usage
-----
>>> from utils.logger import get_logger, log_stage, log_exclusion
>>> logger = get_logger(__name__)
>>> logger.info("Pipeline started")
>>> log_stage("download", "Fetching OpenNeuro datasets")
>>> log_exclusion("sub-001", "SNR below threshold")
"""

import logging
from pathlib import Path
from threading import Lock

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Resolve the project root (two levels up from this file) and ensure the
# ``logs`` directory exists.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_LOG_DIR = _PROJECT_ROOT / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)

# The single log file used by the whole pipeline.
_LOG_FILE = _LOG_DIR / "pipeline.log"

# A lock protects concurrent writes when multiple processes/threads
# happen to use the logger at the same time (e.g., in CI parallel jobs).
_log_lock = Lock()

# ----------------------------------------------------------------------
# Logger creation (singleton pattern)
# ----------------------------------------------------------------------
_LOGGER = None

def _create_logger() -> logging.Logger:
    """
    Internal helper to create and configure the logger.
    The logger writes to ``pipeline.log`` with a concise format that
    includes the timestamp, logger name, level, and message.
    """
    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.INFO)

    # Prevent adding multiple handlers if this function is called again.
    if not logger.handlers:
        # File handler – always appends (do not truncate on each import)
        file_handler = logging.FileHandler(_LOG_FILE, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Also emit to stdout for interactive debugging (optional)
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    return logger

def get_logger(name: str = "pipeline") -> logging.Logger:
    """
    Return a logger instance that writes to ``logs/pipeline.log``.
    The first call creates the singleton; subsequent calls return the
    same instance, ensuring a single log file across the entire
    pipeline.

    Parameters
    ----------
    name: str, optional
        The logger name.  By default the root pipeline logger is used.
        Sub‑modules may pass ``__name__`` to obtain a hierarchical name.

    Returns
    -------
    logging.Logger
        Configured logger.
    """
    global _LOGGER
    if _LOGGER is None:
        with _log_lock:
            if _LOGGER is None:   # Double‑checked locking
                _LOGGER = _create_logger()
    return logging.getLogger(name)

# ----------------------------------------------------------------------
# Convenience helpers
# ----------------------------------------------------------------------
def log_stage(stage: str, message: str) -> None:
    """
    Log a high‑level message associated with a pipeline stage.

    Parameters
    ----------
    stage: str
        Short identifier for the stage (e.g., ``download``, ``preprocess``).
    message: str
        Human‑readable description of what happened in the stage.
    """
    logger = get_logger()
    logger.info(f"[{stage.upper():<12}] {message}")

def log_exclusion(participant_id: str, reason: str) -> None:
    """
    Record that a participant was excluded and why.

    Parameters
    ----------
    participant_id: str
        Identifier of the participant (matches ``participant_id`` column).
    reason: str
        Short description of the exclusion criterion.
    """
    logger = get_logger()
    logger.warning(f"EXCLUDE | participant_id={participant_id} | reason={reason}")

# ----------------------------------------------------------------------
# Ensure the log file exists on import (creates an empty file if missing)
# ----------------------------------------------------------------------
if not _LOG_FILE.exists():
    # Touch the file so that downstream tools can rely on its presence.
    _LOG_FILE.touch()

# Exported symbols for ``from utils.logger import *`` convenience.
__all__ = [
    "get_logger",
    "log_stage",
    "log_exclusion",
]