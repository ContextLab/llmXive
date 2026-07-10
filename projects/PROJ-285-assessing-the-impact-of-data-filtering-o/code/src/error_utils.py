"""
Utility functions for error handling and validation.
"""

import logging
from typing import Any, Optional, List
from .logging_config import get_logger, PipelineError, DataIngestionError

def validate_not_null(value: Any, field_name: str, context: Optional[dict] = None) -> None:
    """
    Validates that a value is not None or empty.
    
    Args:
        value: The value to check.
        field_name: Name of the field for error messaging.
        context: Optional context dictionary for the error.
        
    Raises:
        PipelineError: If the value is None or empty.
    """
    if value is None:
        raise PipelineError(f"Field '{field_name}' cannot be None.", context)
    if isinstance(value, (str, list, dict)) and len(value) == 0:
        raise PipelineError(f"Field '{field_name}' cannot be empty.", context)

def validate_data_frame_columns(df, required_columns: List[str]) -> None:
    """
    Validates that a DataFrame contains all required columns.
    
    Args:
        df: Pandas DataFrame to validate.
        required_columns: List of column names that must exist.
        
    Raises:
        DataIngestionError: If any required column is missing.
    """
    if df is None:
        raise DataIngestionError("DataFrame is None.")
        
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise DataIngestionError(
            f"Missing required columns in DataFrame: {missing}",
            context={"expected": required_columns, "actual": list(df.columns)}
        )

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely performs division, returning a default value if denominator is zero.
    
    Args:
        numerator: The numerator.
        denominator: The denominator.
        default: Value to return if division by zero occurs.
        
    Returns:
        Result of division or default value.
    """
    if denominator == 0:
        logging.getLogger(__name__).warning(f"Division by zero attempted, returning default {default}.")
        return default
    return numerator / denominator
