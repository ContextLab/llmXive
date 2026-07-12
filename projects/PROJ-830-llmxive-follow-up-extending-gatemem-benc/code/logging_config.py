import os
import sys
import logging
import random
from typing import Optional, Any
from datetime import datetime

from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

def setup_logging(name: str = __name__) -> logging.Logger:
    """
    Setup logging configuration.

    Args:
        name: Logger name.

    Returns:
        Configured logger.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # File handler
    log_file = LOG_DIR / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def pin_random_seed(seed: int = 42) -> None:
    """Pin random seed for reproducibility."""
    random.seed(seed)
    if "numpy" in sys.modules:
        import numpy as np
        np.random.seed(seed)
    logger.info(f"Random seed pinned to {seed}")


class ErrorHandling:
    """Context manager for error handling."""

    def __init__(self, logger_name: str):
        self.logger = setup_logging(logger_name)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(f"Error occurred: {exc_val}")
        return False


def verify_log_creation() -> bool:
    """Verify that logs directory exists and is writable."""
    try:
        test_file = LOG_DIR / ".test_write"
        test_file.touch()
        test_file.unlink()
        return True
    except Exception:
        return False
