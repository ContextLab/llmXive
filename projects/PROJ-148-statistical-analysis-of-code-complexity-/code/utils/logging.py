from __future__ import annotations

import logging
import sys
from typing import Optional, Tuple, Dict

_loggers: Dict[str, logging.Logger] = {}


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get or create a logger with the given name.
    Ensures the logger is configured with a console handler if not already.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False

    _loggers[name] = logger
    return logger


def get_project_logger() -> logging.Logger:
    """Convenience function to get the main project logger."""
    return get_logger("llmXive")
