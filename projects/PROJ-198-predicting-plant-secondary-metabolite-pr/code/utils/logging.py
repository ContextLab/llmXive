"""
Simple logging utilities used throughout the project.
Updated to always write a log file (logs/run.log) so that the
configuration loader (T004) creates the required log output.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

_LOGGER = None


def _ensure_log_directory(log_file: Path) -> None:
    """
    Ensure the parent directory for the log file exists.

    Parameters
    ----------
    log_file : Path
        Path to the log file that will be created.
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Configure the root logger.

    Parameters
    ----------
    log_level : str
        Logging level name (e.g. ``"INFO"``).
    log_file : str, optional
        If provided, a file handler writing to this path is added.
        If *None*, a default file ``logs/run.log`` inside the project
        root is created. This guarantees that the `logs/run.log`
        artifact required by the task exists.
    """
    global _LOGGER
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    # Console handler (always present)
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Determine log file path
    if log_file is None:
        # Default to the project's ``logs/run.log`` location.
        # Using a relative path ensures the file is created under the
        # project root, which is the expected location for the task.
        log_path = Path("logs") / "run.log"
    else:
        log_path = Path(log_file)

    # Ensure the directory exists before creating the file handler.
    _ensure_log_directory(log_path)

    # File handler
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    _LOGGER = logger


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger; initialise the global logger if necessary.
    """
    global _LOGGER
    if _LOGGER is None:
        # Initialise with the default configuration (which creates logs/run.log)
        setup_logging()
    return logging.getLogger(name)
