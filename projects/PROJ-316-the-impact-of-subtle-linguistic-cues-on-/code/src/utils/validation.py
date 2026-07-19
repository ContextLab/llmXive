"""
Input validation utilities for the linguistic cues analysis pipeline.

Implements FR-006: Input Validation Logic.
Ensures that input DataFrames contain required columns with correct types
before processing begins.
"""
import pandas as pd
from typing import List, Set, Optional


def validate_input_columns(df: pd.DataFrame, required_cols: List[str]) -> None:
    """
    Validate that the input DataFrame contains all required columns.
    
    This function implements FR-006 by performing strict column validation.
    It checks for the presence of 'text_content' and 'authenticity_score'
    columns (or any other required columns specified).
    
    Args:
        df: The input DataFrame to validate.
        required_cols: List of column names that must be present.
        
    Raises:
        ValueError: If any required column is missing or if the DataFrame
                   is empty/None.
        
    Example:
        >>> df = pd.DataFrame({'text_content': ['hello'], 'authenticity_score': [4.0]})
        >>> validate_input_columns(df, ['text_content', 'authenticity_score'])
        # No exception raised
        
        >>> validate_input_columns(df, ['text_content', 'missing_col'])
        # Raises ValueError
    """
    if df is None:
        raise ValueError("Input DataFrame cannot be None.")
    
    if df.empty:
        raise ValueError("Input DataFrame is empty. At least one row is required.")
    
    if not isinstance(required_cols, (list, set, tuple)):
        raise TypeError("required_cols must be a list, set, or tuple of column names.")
    
    # Convert to set for efficient lookup
    required_set: Set[str] = set(required_cols)
    existing_cols: Set[str] = set(df.columns)
    
    # Find missing columns
    missing: Set[str] = required_set - existing_cols
    
    if missing:
        missing_str = ", ".join(sorted(missing))
        available_str = ", ".join(sorted(existing_cols))
        raise ValueError(
            f"Input DataFrame is missing required columns: {missing_str}. "
            f"Available columns: {available_str}. "
            f"Required columns: {missing_str}."
        )
    
    # Optional: Validate column types for specific known columns
    if 'text_content' in existing_cols:
        if not pd.api.types.is_object_dtype(df['text_content']):
            raise ValueError(
                f"Column 'text_content' must be of object (string) type. "
                f"Found: {df['text_content'].dtype}"
            )
    
    if 'authenticity_score' in existing_cols:
        if not pd.api.types.is_numeric_dtype(df['authenticity_score']):
            raise ValueError(
                f"Column 'authenticity_score' must be of numeric type. "
                f"Found: {df['authenticity_score'].dtype}"
            )
