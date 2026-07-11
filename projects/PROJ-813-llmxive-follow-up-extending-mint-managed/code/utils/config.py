"""
Configuration management and logging infrastructure for llmXive.

This module defines global constants, configuration loading logic,
and a centralized logging setup to ensure consistent observability
across the simulation pipeline.
"""
import logging
import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

# Global Constants
# Default memory limit: 16 GB (16 * 1024^3 bytes)
DEFAULT_MEMORY_LIMIT = 16 * 1024**3
MEMORY_LIMIT_BYTES = DEFAULT_MEMORY_LIMIT

# Default random seed for reproducibility
DEFAULT_SEED: int = 42

# Logging levels mapping
LOG_LEVELS: Dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# Default log file path relative to project root
DEFAULT_LOG_FILE = "data/logs/state.log"
DEFAULT_LOG_LEVEL = "INFO"


def load_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load configuration from a JSON file if it exists.
    Falls back to defaults if the file is missing or invalid.

    Args:
        config_path: Path to the configuration JSON file.

    Returns:
        Dictionary containing configuration parameters.
    """
    default_config = {
        "memory_limit_bytes": MEMORY_LIMIT_BYTES,
        "seed": DEFAULT_SEED,
        "log_level": DEFAULT_LOG_LEVEL,
        "log_file": DEFAULT_LOG_FILE,
    }

    if not config_path:
        # Try to find config in standard locations
        potential_paths = [
            Path("config.json"),
            Path("code/config.json"),
            Path("data/config.json"),
        ]
        for p in potential_paths:
            if p.exists():
                config_path = p
                break

    if config_path:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                # Merge with defaults
                default_config.update(user_config)
        except (json.JSONDecodeError, IOError) as e:
            logging.warning(f"Failed to load config from {config_path}: {e}. Using defaults.")

    return default_config


def setup_logging(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
) -> logging.Logger:
    """
    Configure the root logger with file and console handlers.

    Args:
        log_level: Logging level string (e.g., 'INFO', 'DEBUG').
        log_file: Path to the log file.
        config: Optional full configuration dictionary.

    Returns:
        The configured root logger.
    """
    # Determine settings from arguments or config
    cfg = config or load_config()
    level_str = log_level or cfg.get("log_level", DEFAULT_LOG_LEVEL)
    file_path = log_file or cfg.get("log_file", DEFAULT_LOG_FILE)

    # Ensure log directory exists
    log_path = Path(file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    level = LOG_LEVELS.get(level_str, logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File Handler
    try:
        file_handler = logging.FileHandler(file_path, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        root_logger.addHandler(file_handler)
    except IOError as e:
        print(f"Warning: Could not create log file at {file_path}: {e}")

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    root_logger.addHandler(console_handler)

    return root_logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance, optionally configuring logging if not already done.

    Args:
        name: Logger name (e.g., module name). If None, returns root logger.

    Returns:
        A configured logger instance.
    """
    logger = logging.getLogger(name)
    # If no handlers exist, it means setup_logging hasn't been called yet.
    # We attempt to setup logging with defaults if needed.
    if not logger.handlers and not logging.root.handlers:
        setup_logging()
    return logger
