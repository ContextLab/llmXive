"""
Error handling module for the llmXive project.

Defines custom exceptions and helper functions to raise fatal errors
for specific conditions: "Data Gap" and "Storage Limit Exceeded".
"""

import sys
from typing import Optional

from logging_config import get_logger

# Initialize logger for this module
logger = get_logger(__name__)


class DataGapError(RuntimeError):
    """
    Raised when a required data source is missing or incomplete.
    Corresponds to the 'Data Gap' fatal error condition.
    """
    pass


class StorageLimitExceededError(RuntimeError):
    """
    Raised when disk usage exceeds the defined storage limit.
    Corresponds to the 'Storage Limit Exceeded' fatal error condition.
    """
    pass


def raise_data_gap_error(message: Optional[str] = None) -> None:
    """
    Raises a fatal DataGapError with an optional message.

    Logs the error and terminates the program with exit code 1.

    Args:
        message: Optional specific error message. Defaults to a standard message.
    """
    msg = message or "Data Gap: Required data source is missing or incomplete."
    logger.error(msg)
    raise DataGapError(msg)


def raise_storage_limit_error(message: Optional[str] = None) -> None:
    """
    Raises a fatal StorageLimitExceededError with an optional message.

    Logs the error and terminates the program with exit code 1.

    Args:
        message: Optional specific error message. Defaults to a standard message.
    """
    msg = message or "Storage Limit Exceeded: Disk usage threshold surpassed."
    logger.error(msg)
    raise StorageLimitExceededError(msg)


def check_and_raise_storage_limit(current_usage_gb: float, limit_gb: float) -> None:
    """
    Checks if current disk usage exceeds the limit and raises an error if so.

    Args:
        current_usage_gb: Current disk usage in GB.
        limit_gb: The maximum allowed disk usage in GB.
    """
    if current_usage_gb > limit_gb:
        raise_storage_limit_error(
            f"Storage Limit Exceeded: Current usage {current_usage_gb:.2f} GB "
            f"exceeds limit {limit_gb:.2f} GB."
        )
    logger.debug(f"Disk usage check passed: {current_usage_gb:.2f} GB < {limit_gb:.2f} GB")
