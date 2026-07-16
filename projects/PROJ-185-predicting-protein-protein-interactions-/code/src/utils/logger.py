import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

_logger: Optional[logging.Logger] = None

def get_logger() -> logging.Logger:
    """
    Returns a singleton logger that writes to ``pipeline.log`` in the repository root.
    The logger uses ISO‑8601 timestamps and INFO level by default.
    """
    global _logger
    if _logger is None:
        log_file = Path("pipeline.log")
        logger = logging.getLogger("pipeline")
        logger.setLevel(logging.INFO)

        # Ensure we don't add multiple handlers if get_logger is called repeatedly
        if not logger.handlers:
            handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
            formatter = logging.Formatter(
                fmt="%(asctime)s %(levelname)s %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S%z",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        _logger = logger
    return _logger

def log_cli_invocation(args) -> None:
    """
    Logs the CLI invocation together with the full namespace of arguments.
    """
    logger = get_logger()
    logger.info(f"CLI invoked with args: {args}")

def log_error(message: str) -> None:
    """
    Logs an error message at ERROR level.
    """
    logger = get_logger()
    logger.error(message)
