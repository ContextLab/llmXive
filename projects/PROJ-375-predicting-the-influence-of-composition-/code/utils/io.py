"""
Utility functions for I/O operations used across the pipeline.

Provides:
- ``setup_logging``: configure a simple console logger for the project.
- ``compute_sha256``: return the hexadecimal SHA‑256 hash of a ``bytes`` object.
"""

import logging
import hashlib
from typing import Optional

_LOGGER_CONFIGURED = False

def setup_logging(level: int = logging.INFO, fmt: Optional[str] = None) -> None:
    """
    Configure the root logger with a basic console handler.

    This function is idempotent – calling it multiple times will not add
    duplicate handlers.

    Args:
        level: Logging level for the root logger (default: INFO).
        fmt: Optional logging format string. If not provided, a sensible
             default format is used.
    """
    global _LOGGER_CONFIGURED
    if _LOGGER_CONFIGURED:
        return

    if fmt is None:
        fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    logging.basicConfig(level=level, format=fmt)
    _LOGGER_CONFIGURED = True

def compute_sha256(data: bytes) -> str:
    """
    Compute the SHA‑256 hash of the given ``bytes`` and return the
    hexadecimal digest.

    Args:
        data: Byte string to hash.

    Returns:
        Hexadecimal SHA‑256 digest as a string.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("compute_sha256 expects a bytes-like object")
    return hashlib.sha256(data).hexdigest()