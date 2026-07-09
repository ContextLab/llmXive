"""
Data ingestion, preprocessing, and storage modules.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

# Initialize a project-specific logger
_logger: Optional[logging.Logger] = None

def get_logger(name: str = "llmXive.data") -> logging.Logger:
    """
    Returns a configured logger instance for the data module.
    Ensures a single configured logger per name to avoid duplicate handlers.
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger(name)
        if not _logger.handlers:
            _logger.setLevel(logging.INFO)
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            _logger.addHandler(handler)
            _logger.propagate = False
    return _logger

def init_logging() -> None:
    """
    Global initialization hook to ensure logging is ready before data operations.
    """
    get_logger()

# Export public API
__all__ = ["get_logger", "init_logging"]