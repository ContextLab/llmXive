"""
Logging infrastructure for the project.
"""
import logging
import sys
from pathlib import Path

def setup_logger(name: str = "llmxive", level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a project logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

logger = setup_logger()
