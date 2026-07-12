"""
Logging configuration module for the llmXive pipeline.

This module initializes a global logger that writes to both console and file.
It reads configuration from environment variables defined in the .env file.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Try to load dotenv if available, otherwise proceed with os.environ
try:
    from dotenv import load_dotenv
    # Load from .env if it exists in the project root
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, will rely on os.environ
    pass


def get_env_config() -> dict:
    """
    Reads configuration from environment variables with sensible defaults.

    Returns:
        dict: Configuration dictionary containing DATA_PATH, LOG_LEVEL, and SEED.
    """
    return {
        "data_path": os.getenv("DATA_PATH", "data/raw"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "seed": int(os.getenv("SEED", "42")),
    }


def setup_logger(
    name: Optional[str] = None,
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Configures and returns a logger instance.

    If log_level is not provided, it defaults to the value from the environment
    variable LOG_LEVEL. If log_file is provided, logs are written to that file.

    Args:
        name (str, optional): Logger name. Defaults to 'llmxive'.
        log_level (str, optional): Logging level (e.g., 'INFO'). Defaults to env var.
        log_file (str, optional): Path to log file. Defaults to None (console only).

    Returns:
        logging.Logger: Configured logger instance.
    """
    # Determine logger name
    logger_name = name if name else "llmxive"
    logger = logging.getLogger(logger_name)

    # Avoid adding handlers multiple times if called repeatedly
    if logger.handlers:
        return logger

    # Get log level from argument or environment
    level_str = log_level if log_level else get_env_config()["log_level"]
    level = getattr(logging, level_str.upper(), logging.INFO)
    logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Initialize a default logger for immediate use if imported
default_logger = setup_logger()