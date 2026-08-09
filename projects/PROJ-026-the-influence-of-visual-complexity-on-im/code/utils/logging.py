import logging
import os
from pathlib import Path
from typing import Optional
import sys

from ..config import get_project_root, ensure_directories

def get_log_path() -> Path:
    """Return the path to the logs directory."""
    project_root = get_project_root()
    log_path = project_root / "logs"
    ensure_directories([log_path])
    return log_path

def setup_logging(log_level: int = logging.INFO, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure logging for the project.

    Args:
        log_level: Logging level (default: INFO).
        log_file: Optional filename for file logging. If None, logs only to console.

    Returns:
        The root logger configured.
    """
    logger = logging.getLogger("llmXive")
    logger.setLevel(log_level)

    # Prevent duplicate handlers if setup_logging is called multiple times
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = get_log_path()
        file_path = log_path / log_file
        ensure_directories([file_path.parent])
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(log_level)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name. If None, returns the root logger.

    Returns:
        A configured logger instance.
    """
    if name:
        return logging.getLogger(f"llmXive.{name}")
    return logging.getLogger("llmXive")

def log_counterbalance_strategy(strategy_details: str) -> None:
    """
    Log the specific counterbalancing assignment strategy used.

    This function writes the strategy details to a dedicated log file
    to ensure methodological transparency and reproducibility.

    Args:
        strategy_details: A string describing the counterbalancing strategy,
                          including parameters like seed, split ratio, and order logic.
    """
    logger = setup_logging(log_file="counterbalance_strategy.log")
    logger.info("=== Counterbalancing Strategy Log ===")
    logger.info(strategy_details)
    logger.info("=====================================")
    logger.info("Strategy logged successfully to logs/counterbalance_strategy.log")
