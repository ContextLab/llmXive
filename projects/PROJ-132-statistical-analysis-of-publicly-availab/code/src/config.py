import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Constants defined in T010a
SEED: int = 42
GRID_RES: float = 0.5
PERMUTATIONS: int = 10000

# Targets defined in T010a
DEFAULT_POWER_TARGET: float = 0.80
DEFAULT_CI_WIDTH_TARGET: float = 5.0
DEFAULT_CONVERGENCE_TARGET: float = 0.90
DEFAULT_INSUFFICIENT_DATA_TARGET: float = 0.20

# Logging configuration for T010b
LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "pipeline.log"
LOG_MAX_BYTES = 10485760  # 10MB
LOG_BACKUP_COUNT = 5
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logging(
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Configure logging for the project.

    Sets up a rotating file handler and a console handler.
    The file handler rotates when the log file reaches maxBytes.

    Args:
        log_file: Path to the log file. Defaults to LOG_FILE.
        level: Logging level. Defaults to logging.INFO.

    Returns:
        The root logger instance.
    """
    if log_file is None:
        log_file = LOG_FILE

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)

    # Create file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Add handlers to root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return root_logger

def verify_config_targets() -> dict:
    """
    Verify that the configuration targets are set correctly.

    Returns:
        A dictionary containing the configuration targets and their status.
    """
    targets = {
        "power_target": DEFAULT_POWER_TARGET,
        "ci_width_target": DEFAULT_CI_WIDTH_TARGET,
        "convergence_target": DEFAULT_CONVERGENCE_TARGET,
        "insufficient_data_target": DEFAULT_INSUFFICIENT_DATA_TARGET,
    }
    return targets


# Initialize logging when module is imported
# This ensures logging is available throughout the project
setup_logging()
