import logging
import os
import sys
from pathlib import Path
from typing import Optional

from config import get_project_root, ensure_directories

_logger = None


def get_log_path() -> Path:
    """Get the path to the logs directory."""
    root = get_project_root()
    log_path = root / "logs"
    log_path.mkdir(parents=True, exist_ok=True)
    return log_path


def setup_logging(log_level: int = logging.INFO) -> None:
    """
    Configure logging for the application.

    Args:
        log_level: Logging level (default: INFO)
    """
    global _logger

    if _logger is not None:
        return  # Already configured

    log_path = get_log_path()
    log_file = log_path / "app.log"

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    _logger = True


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    if _logger is None:
        setup_logging()

    return logging.getLogger(name)


def log_counterbalance_strategy(
    seed: int,
    split_ratio: float,
    log_path: Optional[Path] = None
) -> None:
    """
    Log the counterbalance assignment strategy.

    Args:
        seed: Random seed used
        split_ratio: Ratio of participants starting with Low vs High
        log_path: Path to log file
    """
    if log_path is None:
        log_path = get_log_path() / "counterbalance_strategy.log"

    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = get_logger(__name__)

    with open(log_path, 'w') as f:
        f.write("Counterbalance Assignment Strategy\n")
        f.write("=" * 40 + "\n")
        f.write(f"Random Seed: {seed}\n")
        f.write(f"Split Ratio (Low vs High): {split_ratio:.2f}\n")
        f.write(f"Method: Seeded random shuffle\n")
        f.write("=" * 40 + "\n")

    logger.info(f"Logged counterbalance strategy to {log_path}")


if __name__ == "__main__":
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Logging system initialized")
    log_counterbalance_strategy(seed=42, split_ratio=0.5)
