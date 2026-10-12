"""
Simple project‑wide logging configuration.
Provides two helpers:
* ``setup_project_logging(name, logfile)`` – returns a ``logging.Logger`` instance
  configured with a rotating file handler (10 MiB per file, up to 5 backups) and a
  console stream handler.
* ``get_logger(name)`` – convenience wrapper that returns ``logging.getLogger(name)``.
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

def _ensure_parent_dir(path: Path) -> None:
    """Make sure the directory for *path* exists."""
    path.parent.mkdir(parents=True, exist_ok=True)

def setup_project_logging(name: str, logfile: str) -> logging.Logger:
    """
    Configure a logger for the given *name* that writes to *logfile* (relative to the
    project root) and also echoes to ``stderr``.
    The file handler rotates when it reaches 10 MiB, keeping up to 5 backups.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Avoid adding duplicate handlers if this function is called multiple times
    if logger.handlers:
        return logger

    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler with rotation
    log_path = Path(logfile)
    _ensure_parent_dir(log_path)
    file_handler = RotatingFileHandler(
        log_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    logger.debug(f"Logging initialized for {name}; output to {log_path}")
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve (or create) a logger with the given *name*. If the logger has not been
    configured yet, this function will call ``setup_project_logging`` with a default
    logfile under ``logs/<name>.log``.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Default logfile location
        default_logfile = Path("logs") / f"{name}.log"
        setup_project_logging(name, str(default_logfile))
    return logger