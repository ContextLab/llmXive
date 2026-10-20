"""
Project‑wide logger helper.

``get_logger(name)`` returns a ``logging.Logger`` instance that is
pre‑configured according to the project's YAML configuration (see
``code/utils/config.yaml``).  The logger is cached per name so that multiple
calls with the same ``name`` return the identical ``Logger`` object.
"""
import logging
from logging import Logger
from pathlib import Path
from typing import Dict

from .config import get_config
from llmxive_toolkit import paths

_LOGGER_CACHE: Dict[str, Logger] = {}

def _setup_logger(name: str) -> Logger:
    """
    Internal helper that creates and configures a logger instance.

    Parameters
    ----------
    name : str
        Name of the logger (typically ``__name__``).

    Returns
    -------
    logging.Logger
    """
    cfg = get_config()
    log_cfg = cfg.get("logging", {})

    level_name = log_cfg.get("level", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    fmt = log_cfg.get(
        "format",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    datefmt = log_cfg.get("datefmt", "%Y-%m-%d %H:%M:%S")

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if this function is called repeatedly
    if not logger.handlers:
        formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

        # Console (stderr) handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler – path is relative to the project root
        file_rel = log_cfg.get("file", "logs/app.log")
        file_path = paths.root / file_rel
        file_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        logger.debug(
            "Logger '%s' configured – level=%s, file='%s'",
            name,
            level_name,
            file_path,
        )
    return logger

def get_logger(name: str) -> Logger:
    """
    Retrieve a cached logger instance.

    Parameters
    ----------
    name : str
        The logger name (usually ``__name__``).

    Returns
    -------
    logging.Logger
        Configured logger.
    """
    if name not in _LOGGER_CACHE:
        _LOGGER_CACHE[name] = _setup_logger(name)
    return _LOGGER_CACHE[name]
