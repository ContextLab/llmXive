"""
Configuration module for the cosmic ray anisotropy analysis pipeline.

Handles environment variables, default parameters, and validation.
"""
import os
import logging
from typing import Optional

# Default bin size in days (Sidereal day approximation for cosmic ray analysis)
DEFAULT_BIN_SIZE_DAYS = 27

# Validation bounds for bin size
MIN_BIN_SIZE_DAYS = 7
MAX_BIN_SIZE_DAYS = 60

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

logger = logging.getLogger('llmXive')
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def validate_bin_size(bin_size: int) -> bool:
    """
    Validate that the bin size is within acceptable bounds.

    Args:
        bin_size: Bin size in days.

    Returns:
        True if valid.

    Raises:
        ValueError: If bin_size is not an integer or outside [MIN_BIN_SIZE_DAYS, MAX_BIN_SIZE_DAYS].
    """
    if not isinstance(bin_size, int):
        raise ValueError(f"bin_size must be an integer, got {type(bin_size)}")

    if bin_size < MIN_BIN_SIZE_DAYS:
        raise ValueError(
            f"bin_size ({bin_size}) is below minimum ({MIN_BIN_SIZE_DAYS} days)"
        )

    if bin_size > MAX_BIN_SIZE_DAYS:
        raise ValueError(
            f"bin_size ({bin_size}) is above maximum ({MAX_BIN_SIZE_DAYS} days)"
        )

    return True


def get_config_summary() -> dict:
    """
    Return a summary of the current configuration.

    Returns:
        Dictionary with configuration parameters.
    """
    return {
        'default_bin_size_days': DEFAULT_BIN_SIZE_DAYS,
        'min_bin_size_days': MIN_BIN_SIZE_DAYS,
        'max_bin_size_days': MAX_BIN_SIZE_DAYS,
        'log_level': LOG_LEVEL
    }
