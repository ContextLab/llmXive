"""Logging utilities for the Lorentz Violation testing pipeline."""
import logging
import sys
from pathlib import Path
from typing import Optional

from code.config import load_config


def setup_logger(
    name: str = "lorentz_violation",
    level: Optional[int] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Configure and return a logger instance with standardized formatting.

    This function initializes a logger that outputs to both the console
    and optionally to a file. It attempts to load log settings from
    `config.yaml` if available, falling back to sensible defaults.

    Args:
        name: The name of the logger to retrieve or create.
        level: Optional explicit logging level (e.g., logging.DEBUG).
               If None, attempts to load from config, defaults to INFO.
        log_file: Optional path to a log file. If None, only logs to console.

    Returns:
        logging.Logger: A configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times if called repeatedly in same session
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)  # Set to lowest, filter at handler level

    # Determine log level
    log_level = level
    if log_level is None:
        try:
            config = load_config()
            # Config structure: config['logging']['level'] if it exists
            if "logging" in config and "level" in config["logging"]:
                level_str = config["logging"]["level"].upper()
                log_level = getattr(logging, level_str, logging.INFO)
            else:
                log_level = logging.INFO
        except FileNotFoundError:
            log_level = logging.INFO
        except Exception:
            # Fallback if config parsing fails for any reason
            log_level = logging.INFO

    logger.setLevel(log_level)

    # Formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (if requested)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, mode='a')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger