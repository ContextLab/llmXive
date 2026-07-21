import logging
from typing import Any, Optional, List
from .logging_config import get_logger, PipelineError, DataIngestionError

logger = get_logger(__name__)

def validate_not_null(value: Any, field_name: str) -> None:
    """
    Validate that a value is not None.

    Args:
        value: The value to validate.
        field_name: Name of the field for error reporting.

    Raises:
        PipelineError: If the value is None.
    """
    if value is None:
        error_msg = f"Field '{field_name}' cannot be None"
        logger.error(error_msg)
        raise PipelineError(error_msg)


def validate_data_frame_columns(df, required_columns: List[str]) -> None:
    """
    Validate that a DataFrame contains all required columns.

    Args:
        df: The DataFrame to validate.
        required_columns: List of required column names.

    Raises:
        DataIngestionError: If any required column is missing.
    """
    if not hasattr(df, 'columns'):
        error_msg = "Provided object is not a DataFrame"
        logger.error(error_msg)
        raise DataIngestionError(error_msg)

    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        error_msg = f"Missing required columns: {missing_cols}"
        logger.error(error_msg)
        raise DataIngestionError(error_msg)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely perform division, returning a default value if division by zero.

    Args:
        numerator: The numerator.
        denominator: The denominator.
        default: The value to return if division by zero occurs.

    Returns:
        float: The result of division or the default value.
    """
    if denominator == 0:
        logger.warning(f"Division by zero encountered, returning default value {default}")
        return default
    return numerator / denominator
