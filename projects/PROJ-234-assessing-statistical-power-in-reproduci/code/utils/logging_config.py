"""
utils/logging_config.py
-----------------------

Minimal logging configuration used across the pipeline.
Provides a ``setup_logging`` function that returns a logger writing
to a given file (or to ``stderr`` if no path is supplied).  The logger
is configured with a simple formatter and a ``INFO`` level by default.
"""

import logging
from pathlib import Path
from typing import Optional

_loggers = {}

def setup_logging(log_path: Optional[str] = None) -> logging.Logger:
    """
    Configure and return a logger.

    Parameters
    ----------
    log_path : str or None
        If provided, a ``FileHandler`` writing to this path is added.
        The parent directory is created automatically.

    Returns
    -------
    logging.Logger
        A logger named ``'pipeline'`` (singleton per ``log_path``).
    """
    logger_name = "pipeline" if log_path is None else f"pipeline:{log_path}"
    if logger_name in _loggers:
        return _loggers[logger_name]

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # Ensure we don't add duplicate handlers if called multiple times
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        if log_path:
            path = Path(log_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(path, encoding="utf-8")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    _loggers[logger_name] = logger
    return logger

# Optional helper used by some tests
def test_log_entry(message: str, log_path: str) -> bool:
    """
    Write a single log entry to ``log_path`` and verify that the file
    contains the message. Returns ``True`` on success.
    """
    logger = setup_logging(log_path)
    logger.info(message)

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            return message in f.read()
    except Exception:
        return False
