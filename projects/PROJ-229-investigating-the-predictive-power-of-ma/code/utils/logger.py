"""
Logger utility for the project.

Provides a lazily-initialized pipeline logger that writes to a file
(default: ``data/logs/pipeline.log``) and helper functions for the
standard logging levels as well as exception traceback logging.
"""

import logging
import sys
import traceback
from pathlib import Path
from typing import Optional, Dict, Any

import yaml

# Global variable to hold the singleton logger instance
_pipeline_logger: Optional[logging.Logger] = None

# ----------------------------------------------------------------------
# Helper functions to load configuration
# ----------------------------------------------------------------------
def _load_config() -> Dict[str, Any]:
    """
    Load ``config.yaml`` from the project root if it exists.
    Returns an empty dict if the file cannot be read.
    """
    config_path = Path("config.yaml")
    if not config_path.is_file():
        return {}
    try:
        with config_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:  # pragma: no cover – any parsing error is fatal for logging
        return {}

def _get_log_file_path() -> Path:
    """
    Determine the log file location.

    The path can be overridden via a ``log_path`` key in ``config.yaml``.
    If the key is missing, fall back to the default
    ``data/logs/pipeline.log``.
    """
    cfg = _load_config()
    log_path = cfg.get("log_path", "data/logs/pipeline.log")
    return Path(log_path).expanduser().resolve()

# ----------------------------------------------------------------------
# Logger creation
# ----------------------------------------------------------------------
def setup_logger(name: str = "pipeline") -> logging.Logger:
    """
    Create (or retrieve) a configured logger.

    The logger writes to a file with a simple format that includes the
    timestamp, log level and message.  The logger is configured only once;
    subsequent calls return the same instance.
    """
    global _pipeline_logger
    if _pipeline_logger is not None:
        return _pipeline_logger

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # Prevent double logging if root logger has handlers

    log_file = _get_log_file_path()
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Also output to stderr for immediate visibility during CI runs
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    _pipeline_logger = logger
    return logger

# ----------------------------------------------------------------------
# Public accessor
# ----------------------------------------------------------------------
def get_pipeline_logger() -> logging.Logger:
    """
    Return the singleton pipeline logger, creating it on first use.
    """
    if _pipeline_logger is None:
        return setup_logger()
    return _pipeline_logger

# ----------------------------------------------------------------------
# Convenience logging wrappers
# ----------------------------------------------------------------------
def log_debug(message: str) -> None:
    get_pipeline_logger().debug(message)

def log_info(message: str) -> None:
    get_pipeline_logger().info(message)

def log_warning(message: str) -> None:
    get_pipeline_logger().warning(message)

def log_error(message: str) -> None:
    get_pipeline_logger().error(message)

def log_critical(message: str) -> None:
    get_pipeline_logger().critical(message)

def log_exception_details(exc: BaseException, context_msg: str = "") -> None:
    """
    Log an exception with its traceback.

    Parameters
    ----------
    exc : BaseException
        The caught exception.
    context_msg : str, optional
        Additional context to prepend to the traceback.
    """
    logger = get_pipeline_logger()
    if context_msg:
        logger.error(context_msg)
    tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logger.error(tb_str)
