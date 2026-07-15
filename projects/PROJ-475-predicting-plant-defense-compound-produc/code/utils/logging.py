"""
Logging Utility.
"""
import logging
import sys
from pathlib import Path
from typing import Optional, Union

def get_logger(name: str) -> logging.Logger:
    """Gets a logger by name."""
    return logging.getLogger(name)

def configure_root_logger(level: int = logging.INFO):
    """Configures the root logger."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def get_module_logger(name: str) -> logging.Logger:
    """Gets a module-specific logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    return logger
