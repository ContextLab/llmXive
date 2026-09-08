import logging
import os
import sys
from pathlib import Path
from typing import Optional
from config import get_project_root, ensure_directories

def get_log_path() -> Path:
    """Get the path to the logs directory."""
    project_root = get_project_root()
    log_path = project_root / "logs"
    ensure_directories([log_path])
    return log_path

def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_str: Optional[str] = None,
) -> logging.Logger:
    """
    Set up logging configuration.

    Args:
        level: Logging level (default: INFO)
        log_file: Optional log file path (default: logs/app.log)
        format_str: Optional format string (default: standard format)

    Returns:
        Root logger instance
    """
    if format_str is None:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    if log_file is None:
        log_path = get_log_path()
        log_file = str(log_path / "app.log")

    # Ensure log directory exists
    ensure_directories([Path(log_file).parent])

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(format_str))
    root_logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(format_str))
    root_logger.addHandler(console_handler)

    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)

def log_counterbalance_strategy(seed: int, split_ratio: float, log_file: Optional[str] = None) -> None:
    """
    Log the counterbalancing assignment strategy used.

    Args:
        seed: Random seed used for shuffling
        split_ratio: Ratio of participants assigned to each order (e.g., 0.5 for 50/50)
        log_file: Optional specific log file path (default: logs/counterbalance_strategy.log)
    """
    if log_file is None:
        log_path = get_log_path()
        log_file = str(log_path / "counterbalance_strategy.log")

    # Ensure log directory exists
    ensure_directories([Path(log_file).parent])

    logger = logging.getLogger("counterbalance")
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler for counterbalance strategy
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(file_handler)

    # Log the strategy
    logger.info(f"Counterbalancing Assignment Strategy")
    logger.info(f"====================================")
    logger.info(f"Random Seed: {seed}")
    logger.info(f"Split Ratio: {split_ratio:.2f} (Low-High vs High-Low)")
    logger.info(f"Method: Seeded random shuffle (numpy.random.default_rng)")
    logger.info(f"Timestamp: {logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None))}")
    logger.info(f"====================================")
    logger.info("")