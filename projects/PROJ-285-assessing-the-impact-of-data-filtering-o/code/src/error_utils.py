import logging
from typing import Any, Optional, List

from .logging_config import get_logger, DataIngestionError, ThresholdFilterError

logger = get_logger(__name__)


def validate_not_null(value: Any, field_name: str, context: str = "") -> Any:
    """
    Validates that a value is not None.
    Raises DataIngestionError if validation fails.
    """
    if value is None:
        msg = f"Validation failed in {context}: '{field_name}' is None."
        logger.error(msg)
        raise DataIngestionError(msg)
    return value


def validate_data_frame_columns(df: Any, required_columns: List[str], context: str = "") -> bool:
    """
    Validates that a DataFrame contains all required columns.
    Returns True if valid, raises DataIngestionError if missing columns.
    """
    if not hasattr(df, 'columns'):
        msg = f"Validation failed in {context}: Object is not a DataFrame."
        logger.error(msg)
        raise DataIngestionError(msg)

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        msg = f"Validation failed in {context}: Missing columns {missing}."
        logger.error(msg)
        raise DataIngestionError(msg)
    
    logger.debug(f"Validation passed in {context}: All required columns present.")
    return True


def safe_divide(numerator: float, denominator: float, default: float = 0.0, context: str = "") -> float:
    """
    Performs division safely. Returns default if denominator is zero.
    Logs a warning if division by zero occurs.
    """
    if denominator == 0:
        logger.warning(f"Division by zero in {context}: returning {default}.")
        return default
    return numerator / denominator
