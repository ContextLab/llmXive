"""
Logging utilities for the project.

Provides a `get_logger` function that returns a logger configured to write
timestamped messages to both the console and a rotating log file located at
``logs/pipeline.log``. Also provides a simple `setup_logging` helper for
configuring the root logger if needed.

The implementation uses :class:`logging.handlers.RotatingFileHandler` to
rotate the log file when it exceeds 5 MiB, keeping up to five backup files.
This satisfies the requirement for log rotation while ensuring that the
log file is always created under the project's ``logs`` directory.
"""

import logging
from logging.handlers import RotatingFileHandler
from llmxive_toolkit import paths

# Define the path to the pipeline log file using the llmxive toolkit helper.
_log_path = paths.logs("pipeline.log")
# Ensure the parent directory exists.
_log_path.parent.mkdir(parents=True, exist_ok=True)

# Rotation settings: 5 MiB per file, keep 5 backups.
_MAX_BYTES = 5 * 1024 * 1024  # 5 MiB
_BACKUP_COUNT = 5

def _ensure_handler(logger: logging.Logger) -> None:
    """
    Attach console and rotating file handlers to ``logger`` if they are not
    already present.

    This function is idempotent: calling it multiple times will not add
    duplicate handlers.
    """
    if any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        # Handlers already configured.
        return

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )

    # Console handler (stderr)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Rotating file handler
    file_handler = RotatingFileHandler(
        filename=_log_path,
        mode="a",
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a logger with the given ``name`` that writes to both the console
    and the rotating pipeline log file.

    The logger's level is set to ``INFO`` by default. Handlers are added only
    once per logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    _ensure_handler(logger)
    return logger

def setup_logging(level: int = logging.INFO) -> None:
    """
    Convenience function to configure the root logger. This is useful for
    scripts that want to ensure a consistent logging configuration without
    manually calling :func:`get_logger` for the root logger.

    Parameters
    ----------
    level : int, optional
        Logging level for the root logger (default: ``logging.INFO``).
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    _ensure_handler(root_logger)