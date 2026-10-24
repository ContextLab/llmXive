"""
Utility functions for I/O operations used across the pipeline.

This module provides:
- `compute_sha256(data: bytes) -> str`: Compute SHA‑256 hex digest of binary data.
- `setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> None`:
  Configure a basic console (and optional file) logger for the project.

The functions are deliberately lightweight and have no external dependencies
beyond the Python standard library, ensuring they work in the constrained
execution environment.
"""

import logging
import hashlib
from pathlib import Path
from typing import Optional

__all__ = ["compute_sha256", "setup_logging"]

def compute_sha256(data: bytes) -> str:
    """
    Compute the SHA‑256 hash of the given binary ``data`` and return the
    hexadecimal digest string.

    Parameters
    ----------
    data: bytes
        Binary data to hash.

    Returns
    -------
    str
        Hexadecimal SHA‑256 digest.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("compute_sha256 expects a bytes-like object")
    return hashlib.sha256(data).hexdigest()


def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> None:
    """
    Initialise a simple logging configuration for the project.

    - Logs to the console (stderr) with a concise format.
    - Optionally logs to a file if ``log_file`` is supplied; the file is
      created inside the project ``logs`` directory via ``llmxive_toolkit``.
    - The function is idempotent: calling it multiple times will not add
      duplicate handlers.

    Parameters
    ----------
    log_file: Optional[Path]
        Path to a log file. If ``None`` (default) only console logging is set.
    level: int
        Logging level (e.g., ``logging.INFO``). Defaults to ``INFO``.
    """
    logger = logging.getLogger()
    if logger.handlers:
        # Assume logging has already been configured elsewhere.
        return

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Optional file handler
    if log_file is not None:
        # Ensure parent directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.setLevel(level)
