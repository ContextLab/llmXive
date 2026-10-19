"""
Simple logging utilities used throughout the project.

Provides:
  * configure_logger(level: str) – sets up a basic console logger.
  * get_logger(name) – returns a logger instance.
"""

import logging

_LOGGER = None

def configure_logger(level: str = "INFO"):
    """Configure the root logger with a simple format."""
    global _LOGGER
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s – %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    _LOGGER = logging.getLogger()
    return _LOGGER

def get_logger(name: str):
    """Return a logger with the given name, creating the root logger if needed."""
    global _LOGGER
    if _LOGGER is None:
        configure_logger()
    return logging.getLogger(name)
