"""
Logging infrastructure for the llmXive research pipeline.

Provides a configurable logging setup that writes to both console and file,
with automatic log rotation and structured formatting.
"""
import logging
from pathlib import Path
from typing import Optional

from config import get_config


def setup_logging(
    level: Optional[int] = None,
    log_dir: Optional[Path] = None,
    log_file: Optional[str] = None,
    console: bool = True,
) -> logging.Logger:
    """
    Configure the root logger with file and console handlers.

    Args:
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
               Defaults to Config.LOG_LEVEL if not provided.
        log_dir: Directory for log files. Defaults to Config.LOGS_ROOT.
        log_file: Log filename. Defaults to "run.log" if not provided.
        console: Whether to add a console handler. Defaults to True.

    Returns:
        The root logger instance.
    """
    config = get_config()

    # Resolve logging level
    # Config stores the level as a string like "INFO"; map it to the logging constant.
    config_level_name = config.get("log_level", "INFO")
    effective_level = level or getattr(logging, config_level_name.upper(), logging.INFO)

    # Resolve log directory
    # Prefer explicit argument, then config's logs_root, finally fallback to "logs".
    log_dir_path = Path(log_dir) if log_dir else Path(config.get("logs_root", "logs"))
    log_dir_path.mkdir(parents=True, exist_ok=True)

    # Resolve log file name
    # Config may provide a custom name; otherwise default to "run.log".
    log_file_name = log_file or config.get("log_file", "run.log")
    log_path = log_dir_path / log_file_name

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(effective_level)

    # Clear existing handlers to avoid duplicate logs on repeated calls
    root_logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler (no rotation needed for the simple use‑case; can be extended later)
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(effective_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Optional console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(effective_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Log startup message
    root_logger.info(
        f"Logging initialized: level={effective_level}, file={log_path}"
    )

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance by name.

    Args:
        name: Logger name (typically __name__ of the module).

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)