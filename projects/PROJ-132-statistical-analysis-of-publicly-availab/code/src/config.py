"""
Configuration module for the Bird Migration Climate Correlation project.

This module defines global constants, logging configuration, and target thresholds
for success criteria validation.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
INTERIM_DIR = DATA_DIR / "interim"
RAW_DIR = DATA_DIR / "raw"

# --- Constants (T010 Requirement) ---
# Random seed for reproducibility
SEED: int = 42

# Grid resolution in degrees
GRID_RES: float = 0.5

# Number of permutations for statistical tests
PERMUTATIONS: int = 10000

# NOTE: SAMPLE_SIZE=1000 has been removed as per T010 requirements.
# Actual sample sizes are now determined by the real data stream.

# --- Success Criteria Targets (T001 & T047 Requirement) ---
# These are the numeric targets for validation checks.
POWER_TARGET: float = 0.80
CI_WIDTH_TARGET: float = 5.0
CONVERGENCE_TARGET: float = 0.90
INSUFFICIENT_DATA_TARGET: float = 0.20

# --- Logging Configuration ---
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

def setup_logging(name: str = "bird_migration", level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger with file and console handlers.

    Args:
        name: Logger name (default: "bird_migration")
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Ensure log directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"{name}.log"

    # File Handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def verify_config_targets() -> bool:
    """
    Verify that all target constants are set to non-negative, valid values.

    Returns:
        True if all targets are valid, False otherwise.
    """
    checks = [
        POWER_TARGET >= 0.0 and POWER_TARGET <= 1.0,
        CI_WIDTH_TARGET > 0.0,
        CONVERGENCE_TARGET >= 0.0 and CONVERGENCE_TARGET <= 1.0,
        INSUFFICIENT_DATA_TARGET >= 0.0 and INSUFFICIENT_DATA_TARGET <= 1.0,
    ]
    return all(checks)

# Initialize main logger
logger = setup_logging()

# Verification: Write a test log entry to ensure format compliance
logger.debug("Configuration module loaded. Verifying targets...")
if not verify_config_targets():
    logger.error("Configuration targets failed verification.")
else:
    logger.info("Configuration targets verified successfully.")
