"""
Utility functions shared across the project.

This module provides:
- get_logger: configure and retrieve a logger.
- log_stage: helper to log a standardized stage message.
- ensure_directory: guarantee that a directory exists.
- safe_divide: division with graceful handling of zero denominator.
- set_global_seed: deterministic seeding for numpy and random.
"""

import logging
import os
import random
from pathlib import Path
from typing import Optional

__all__ = [
    "get_logger",
    "log_stage",
    "ensure_directory",
    "safe_divide",
    "set_global_seed",
]


def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a configured logger.

    Parameters
    ----------
    name : str
        Name of the logger (usually ``__name__``).
    log_file : str, optional
        If provided, a file handler is attached that writes to ``log_file``.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        # Logger already configured – avoid duplicate handlers.
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Stream handler (stderr)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Optional file handler
    if log_file:
        file_path = Path(log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_stage(
    logger: logging.Logger,
    task_id: str,
    stage_name: str,
    message: str,
    level: str = "INFO",
) -> None:
    """
    Log a standardized stage message.

    The format is ``[<TASK_ID>] <STAGE_NAME>: <MESSAGE>``.

    Parameters
    ----------
    logger : logging.Logger
        Logger to emit the message.
    task_id : str
        Identifier of the task (e.g., ``T012``).
    stage_name : str
        Human‑readable name of the stage.
    message : str
        Message describing the event.
    level : str, optional
        Logging level name (``INFO``, ``WARNING``, ``ERROR``, …).
        Defaults to ``INFO``.
    """
    level = level.upper()
    if not hasattr(logging, level):
        level = "INFO"
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(f"[{task_id}] {stage_name}: {message}")


def ensure_directory(path: Path) -> None:
    """
    Ensure that ``path`` exists and is a directory.

    Parameters
    ----------
    path : pathlib.Path
        Directory path to create if it does not exist.
    """
    path.mkdir(parents=True, exist_ok=True)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Divide two numbers safely.

    Returns ``default`` when ``denominator`` is zero (or very close to zero).

    Parameters
    ----------
    numerator : float
    denominator : float
    default : float, optional
        Value to return when division is not possible. Defaults to ``0.0``.

    Returns
    -------
    float
    """
    try:
        if abs(denominator) < 1e-12:
            return default
        return numerator / denominator
    except Exception:
        return default


def set_global_seed(seed: int) -> None:
    """
    Seed the global random number generators used in the project.

    Parameters
    ----------
    seed : int
        Seed value.
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        # Numpy may not be available in very constrained environments;
        # the import is guarded to keep the function safe.
        pass
