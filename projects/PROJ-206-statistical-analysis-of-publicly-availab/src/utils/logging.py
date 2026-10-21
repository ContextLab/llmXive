"""
Utility module for configuring and retrieving loggers throughout the project.

Provides:
  - get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger
  - set_log_level(level: Union[str, int]) -> None
The implementation is deliberately lightweight and avoids any side‑effects that
could interfere with the CI environment. It uses the standard library `logging`
module and creates a console handler by default. If a `log_file` path is
supplied, a rotating file handler is added.
"""
import logging
import sys
from pathlib import Path
from typing import Optional, Union

# Create a module‑level logger cache to avoid duplicate handlers
_loggers = {}


def _ensure_log_file_dir(log_file: Path) -> None:
    """
    Ensure the parent directory for the log file exists.
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)


def set_log_level(level: Union[str, int]) -> None:
    """
    Set the logging level for the root logger.

    Parameters
    ----------
    level : Union[str, int]
        Logging level name (e.g., "INFO") or numeric value (e.g., logging.INFO).
    """
    logging.getLogger().setLevel(level)


def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a configured logger.

    Parameters
    ----------
    name : str
        Name of the logger (typically ``__name__``).
    log_file : Optional[str], default None
        If provided, a rotating file handler will be attached that writes to
        the given path. The directory hierarchy is created automatically.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Console handler (stderr) – ensures messages appear in CI logs
    console_handler = logging.StreamHandler(stream=sys.stderr)
    console_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Optional file handler
    if log_file:
        log_path = Path(log_file).expanduser().resolve()
        _ensure_log_file_dir(log_path)
        file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
        file_formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Avoid propagating to the root logger (prevents duplicate lines)
    logger.propagate = False

    _loggers[name] = logger
    return logger
