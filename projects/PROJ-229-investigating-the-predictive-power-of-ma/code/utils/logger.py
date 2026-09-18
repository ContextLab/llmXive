"""
Logger utility for the project.

Provides a singleton pipeline logger that writes to a file defined in
``config.yaml`` under the key ``log_file``. If the configuration does not
specify a log file, a default location ``data/logs/pipeline.log`` is used.

The helper functions ``log_debug``, ``log_info`` etc. are thin wrappers
around the standard :pyclass:`logging.Logger` methods and automatically
initialise the logger on first use.
"""

import logging
import sys
import traceback
from pathlib import Path
from typing import Optional, Dict, Any

# The config module loads ``config.yaml`` and provides ``get_config``.
# Import is placed inside a function to avoid import‑time side effects if
# ``config.yaml`` is missing or malformed; any error will be raised when
# the logger is first set up.
def _load_config() -> Dict[str, Any]:
    try:
        from config import get_config
    except Exception as exc:
        # If the config module cannot be imported we fall back to an empty
        # configuration – the logger will use its default path.
        return {}
    try:
        return get_config()
    except Exception:
        # Any problem reading the config (e.g. missing file) results in an
        # empty dict so the logger can still operate.
        return {}

_logger: Optional[logging.Logger] = None

def _ensure_log_directory(log_path: Path) -> None:
    """Create parent directories for the log file if they do not exist."""
    log_path.parent.mkdir(parents=True, exist_ok=True)

def setup_logger(level: int = logging.INFO) -> logging.Logger:
    """
    Initialise the singleton pipeline logger.

    Parameters
    ----------
    level: int, optional
        Logging level; defaults to ``logging.INFO``.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    global _logger
    if _logger is not None:
        return _logger

    config = _load_config()
    log_file = config.get("log_file", "data/logs/pipeline.log")
    log_path = Path(log_file)

    _ensure_log_directory(log_path)

    logger = logging.getLogger("pipeline")
    logger.setLevel(level)
    logger.propagate = False  # Prevent double logging in notebooks/tests

    # File handler
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Stream handler (stderr) for immediate feedback
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_formatter = logging.Formatter("%(levelname)s - %(message)s")
    stream_handler.setFormatter(stream_formatter)
    logger.addHandler(stream_handler)

    _logger = logger
    return logger

def get_pipeline_logger() -> logging.Logger:
    """
    Return the singleton pipeline logger, creating it on first use.
    """
    if _logger is None:
        return setup_logger()
    return _logger

# Convenience wrappers -----------------------------------------------------

def log_debug(message: str) -> None:
    """Log a DEBUG level message."""
    get_pipeline_logger().debug(message)

def log_info(message: str) -> None:
    """Log an INFO level message."""
    get_pipeline_logger().info(message)

def log_warning(message: str) -> None:
    """Log a WARNING level message."""
    get_pipeline_logger().warning(message)

def log_error(message: str) -> None:
    """Log an ERROR level message."""
    get_pipeline_logger().error(message)

def log_critical(message: str) -> None:
    """Log a CRITICAL level message."""
    get_pipeline_logger().critical(message)

def log_exception_details(exc: BaseException, context: str = "") -> None:
    """
    Log an exception with its traceback.

    Parameters
    ----------
    exc: BaseException
        The caught exception instance.
    context: str, optional
        Additional context message to prepend to the traceback.
    """
    logger = get_pipeline_logger()
    tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
    tb_text = "".join(tb_lines)
    if context:
        logger.error("%s\n%s", context, tb_text)
    else:
        logger.error("%s", tb_text)
