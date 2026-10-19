"""
Logging infrastructure setup.
Provides centralized logger configuration and specific logging helpers for
negation exclusions and abort conditions.
This logger writes to a per‑process log file (e.g., logs/run_<pid>.log) to
avoid race conditions when multiple processes are logging concurrently.
"""
import logging
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from code.config import PROJECT_ROOT

# Ensure the logs directory exists under the project root.
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def _log_file_path(name: str) -> Path:
    """
    Construct a log file path that is unique to the current OS process.

    The filename includes the logger ``name`` for readability, the current
    process ID (PID) to guarantee per‑process isolation, and a timestamp
    to avoid overwriting logs from repeated runs of the same process.

    Args:
        name: The logical name of the logger (e.g., ``"pipeline"``).

    Returns:
        A :class:`pathlib.Path` pointing to the log file inside ``LOGS_DIR``.
    """
    pid = os.getpid()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_pid{pid}_{timestamp}.log"
    return LOGS_DIR / filename

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up (or retrieve) a logger with both console and per‑process file
    handlers.

    The function is idempotent: if the logger already has handlers attached,
    it returns the existing logger without adding duplicate handlers.

    Args:
        name: Identifier for the logger (used for both the logger name and
              the log file prefix).
        level: Logging level; defaults to :data:`logging.INFO`.

    Returns:
        A configured :class:`logging.Logger` instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # If handlers are already attached, assume the logger has been set up.
    if logger.handlers:
        return logger

    # Formatter shared by both handlers.
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (stdout) for immediate feedback.
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler writes to a per‑process log file.
    file_handler = logging.FileHandler(_log_file_path(name))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

def log_negation_exclusion(logger: logging.Logger, comment_id: str, reason: str):
    """
    Log a comment exclusion due to negation rules.

    Args:
        logger: The logger instance to use.
        comment_id: Identifier of the comment being excluded.
        reason: Human‑readable explanation for the exclusion.
    """
    logger.warning(f"NEGATION EXCLUSION | ID: {comment_id} | Reason: {reason}")

def log_abort_condition(logger: logging.Logger, reason: str, condition_name: str):
    """
    Log a critical abort condition that stops pipeline execution.

    Args:
        logger: The logger instance to use.
        reason: Explanation of why the abort is triggered.
        condition_name: Short name of the condition that failed.
    """
    logger.critical(f"ABORT CONDITION TRIGGERED: {condition_name}")
    logger.critical(f"Reason: {reason}")

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve an existing logger or create a new one if it does not exist.

    This helper mirrors :func:`logging.getLogger` but is kept for API
    compatibility with other modules in the project.

    Args:
        name: Logger name.

    Returns:
        A :class:`logging.Logger` instance.
    """
    return logging.getLogger(name)