"""Centralized logging infrastructure for the project.

``setup_logger(name)`` configures a console handler (stdout) and, when
the environment variable ``FID_LOG_FILE`` is set (or a log file path is
passed explicitly), an additional file handler under the project tree.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def _resolve_log_file(explicit_path: Optional[str]) -> Optional[Path]:
    """Determine the log file location, if any."""
    if explicit_path:
        return Path(explicit_path)
    env_path = os.environ.get("FID_LOG_FILE")
    if env_path:
        return Path(env_path)
    return None


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """Initialize and return a logger with console (and optional file) output.

    Args:
        name: Logger name (usually ``__name__``).
        level: Logging level (default INFO).
        log_file: Optional path to also write log records to a file.

    Returns:
        A configured :class:`logging.Logger`.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if logger.handlers:
        # Already configured; just make sure the level is respected.
        logger.setLevel(level)
        return logger

    formatter = logging.Formatter(LOG_FORMAT)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_target = _resolve_log_file(log_file)
    if file_target is not None:
        try:
            file_target.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(file_target)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError:
            # File logging is best-effort; console logging still works.
            pass

    logger.propagate = False
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a configured logger for ``name`` (defaults to this module)."""
    if name is None:
        name = __name__
    return setup_logger(name)


def main() -> None:
    logger = get_logger("logger_selftest")
    logger.info("Logger test")


if __name__ == "__main__":
    main()
