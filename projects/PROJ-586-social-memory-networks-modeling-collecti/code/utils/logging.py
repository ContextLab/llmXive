"""
utils/logging.py
-----------------

Simple wrapper around the standard library ``logging`` module that configures
a file‑based logger used by the experiment scripts.  The original implementation
already existed; this file is included here to guarantee that the import
``from utils.logging import setup_logger`` works without modification.
"""

import logging
from pathlib import Path
from typing import Optional

def setup_logger(log_file: Path | str, level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger that writes to ``log_file``.
    The logger is singleton‑style – repeated calls return the same instance.
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("experiment_logger")
    logger.setLevel(level)

    # Prevent adding multiple handlers if ``setup_logger`` is called repeatedly
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
