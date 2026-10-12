"""
Logging configuration utilities for the project.

This module provides a small, consistent API used throughout the codebase:
- ``get_logger``: obtain a logger instance with optional file output.
- ``setup_logging``: convenience wrapper that creates a logger whose
  file handler lives under ``data/logs/<name>.log``.
- ``setup_project_logging``: legacy helper used by the original
  ``01_data_curation.py`` script (kept for backward compatibility).

All loggers emit to ``stdout`` (or ``sys.stderr``) and to a file when a
path is supplied. Directories are created on‑demand. The implementation
deliberately avoids any external configuration files so that imports work
in the isolated execution environment.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

__all__ = [
    "get_logger",
    "setup_logging",
    "setup_project_logging",
]

def _ensure_parent_dir(path: Path) -> None:
    """Make sure the directory for *path* exists."""
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)

def get_logger(name: str, log_file: Optional[Path] = None) -> logging.Logger:
    """
    Create (or retrieve) a logger with the given *name*.

    Parameters
    ----------
    name: str
        Name of the logger (usually ``__name__``).
    log_file: Path | None
        If provided, a ``FileHandler`` writing to *log_file* is added.
        The parent directory is created automatically.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if this function is called multiple times
    if getattr(logger, "_configured", False):
        return logger

    logger.setLevel(logging.INFO)

    # Stream handler (stdout) – always present
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(stream_handler)

    # Optional file handler
    if log_file is not None:
        _ensure_parent_dir(log_file)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(file_handler)

    # Mark as configured to prevent duplicate handlers
    logger._configured = True  # type: ignore[attr-defined]
    return logger

def setup_logging(name: str) -> logging.Logger:
    """
    Convenience wrapper that creates a logger whose output file lives under
    ``data/logs/<name>.log``.

    Parameters
    ----------
    name: str
        Logical name for the logger (e.g., ``"visualization"``).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    log_path = Path("data") / "logs" / f"{name}.log"
    return get_logger(name, log_path)

def setup_project_logging(project_name: str, log_path: str) -> logging.Logger:
    """
    Legacy helper retained for backward compatibility with existing scripts.
    It mirrors the original ``setup_project_logging`` signature used in
    ``code/01_data_curation.py``.

    Parameters
    ----------
    project_name: str
        Identifier for the logging context (unused beyond naming).
    log_path: str
        Destination file for the log output.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    # ``log_path`` may be a string; convert to ``Path`` for consistency.
    log_file = Path(log_path)
    return get_logger(project_name, log_file)
