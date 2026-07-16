"""
Input validation utilities for the linguistic cues analysis pipeline.

Implements FR-006: Strict validation of input data schemas to prevent
downstream errors and ensure data integrity.
"""
import pandas as pd
from typing import List, Set, Optional


def validate_input_columns(df: pd.DataFrame, required_cols: List[str]) -> None:
    """
    Validate that a DataFrame contains all required columns.
    
    This function enforces FR-006 by strictly checking for the presence
    of specified columns and raising a clear ValueError if any are missing.
    
    Args:
        df: The DataFrame to validate.
        required_cols: List of column names that must be present.
        
    Raises:
        ValueError: If any required columns are missing from the DataFrame.
                    The error message lists exactly which columns are missing.
                    
    Example:
        >>> df = pd.DataFrame({'text_content': ['hello'], 'authenticity_score': [4]})
        >>> validate_input_columns(df, ['text_content', 'authenticity_score'])
        # No exception raised
        
        >>> validate_input_columns(df, ['text_content', 'missing_col'])
        # Raises ValueError: Missing required columns: ['missing_col']
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}")
        
    if not required_cols:
        # No validation needed if no columns specified
        return
        
    current_columns = set(df.columns)
    required_set = set(required_cols)
    missing_cols = required_set - current_columns
    
    if missing_cols:
        missing_list = sorted(list(missing_cols))
        raise ValueError(
            f"Missing required columns in input DataFrame: {missing_list}. "
            f"Available columns: {sorted(list(current_columns))}. "
            f"Required columns: {sorted(list(required_set))}. "
            "This validation is mandated by FR-006 to ensure data integrity."
        )
    
    # Optional: Log successful validation for debugging
    # (In a real implementation, this might use the project's logging setup)
    # logging.debug(f"Input validation passed: all required columns present")
