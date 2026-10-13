"""
setup_logging.py
----------------
Centralized logging utilities for the project.

Provides three logger factories:
  * get_data_quality_logger()      – logs data‑quality messages.
  * get_exclusion_logger()        – logs records excluded during ingestion.
  * get_model_diagnostics_logger() – logs diagnostics from the modeling step.

All loggers write to files under the ``results/logs`` directory and also emit
to the console. The log files are created lazily; the parent directory is
guaranteed to exist by ``config.py``.
"""
import logging
import sys
from pathlib import Path

from llmxive_toolkit import paths

# Ensure the log directory exists (config.py already creates it, but we are defensive)
LOG_DIR = paths.results("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

def _configure_logger(name: str, logfile: Path) -> logging.Logger:
    """
    Internal helper to create (or retrieve) a logger with a file handler.

    Parameters
    ----------
    name: str
        The logger name.
    logfile: Path
        Path to the log file (will be created if missing).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid adding duplicate handlers if this function is called multiple times.
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(logfile) for h in logger.handlers):
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Console handler (stdout)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler
        file_handler = logging.FileHandler(logfile, mode="a")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def get_data_quality_logger() -> logging.Logger:
    """
    Logger for data‑quality validation steps.

    Returns
    -------
    logging.Logger
    """
    logfile = LOG_DIR / "data_quality.log"
    return _configure_logger("data_quality", logfile)

def get_exclusion_logger() -> logging.Logger:
    """
    Logger for records excluded during ingestion / preprocessing.

    Returns
    -------
    logging.Logger
    """
    logfile = LOG_DIR / "exclusion.log"
    return _configure_logger("exclusion", logfile)

def get_model_diagnostics_logger() -> logging.Logger:
    """
    Logger for model fitting diagnostics (convergence, warnings, etc.).

    Returns
    -------
    logging.Logger
    """
    logfile = LOG_DIR / "model_diagnostics.log"
    return _configure_logger("model_diagnostics", logfile)
