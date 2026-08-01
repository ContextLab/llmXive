"""
Input validation utilities for the linguistic cues analysis pipeline.

This module implements strict input validation as mandated by FR-006,
ensuring that data frames contain required columns with correct types
before processing begins.
"""

import pandas as pd
from typing import List, Set, Optional


def validate_input_columns(df: pd.DataFrame, required_cols: List[str]) -> None:
    """
    Validate that a DataFrame contains all required columns.

    This function enforces FR-006 by checking for the presence of critical
    columns needed for analysis. If any required column is missing, it raises
    a clear ValueError with details about what is missing.

    Parameters
    ----------
    df : pd.DataFrame
        The input DataFrame to validate.
    required_cols : List[str]
        List of column names that must be present in the DataFrame.

    Raises
    ------
    ValueError
        If the DataFrame is empty, or if any required column is missing.
        The error message clearly specifies which columns are missing.

    Examples
    --------
    >>> import pandas as pd
    >>> df = pd.DataFrame({'text_content': ['hello'], 'authenticity_score': [4.0]})
    >>> validate_input_columns(df, ['text_content', 'authenticity_score'])
    # No exception raised

    >>> df_missing = pd.DataFrame({'text_content': ['hello']})
    >>> validate_input_columns(df_missing, ['text_content', 'authenticity_score'])
    ValueError: Missing required columns: ['authenticity_score']
    """
    if df.empty:
        raise ValueError("Input DataFrame is empty. Cannot validate columns on empty data.")

    existing_cols = set(df.columns)
    required_set = set(required_cols)
    missing_cols = required_set - existing_cols

    if missing_cols:
        missing_list = sorted(list(missing_cols))
        raise ValueError(
            f"Missing required columns: {missing_list}. "
            f"Expected columns: {required_list}, found: {sorted(list(existing_cols))}"
        )

    # Optional: Check for column type consistency if needed in future
    # For now, FR-006 focuses on column presence

# Explicitly define required columns for common use cases
REQUIRED_FOR_AUTHENTICITY_ANALYSIS = ['text_content', 'authenticity_score']
REQUIRED_FOR_FEATURE_EXTRACTION = ['conversation_id', 'text_content']
REQUIRED_FOR_CORRELATION = ['text_content', 'authenticity_score', 'first_person_count', 'hedge_count', 'sentiment_score']


def validate_authenticity_dataframe(df: pd.DataFrame) -> None:
    """
    Validate a DataFrame for authenticity analysis (FR-006 compliance).

    Checks specifically for the columns required to perform authenticity
    correlation and regression analyses.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to validate.

    Raises
    ------
    ValueError
        If 'text_content' or 'authenticity_score' columns are missing.
    """
    validate_input_columns(df, REQUIRED_FOR_AUTHENTICITY_ANALYSIS)


def validate_feature_dataframe(df: pd.DataFrame) -> None:
    """
    Validate a DataFrame for feature extraction output.

    Checks for the columns produced by the extraction pipeline.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to validate.

    Raises
    ------
    ValueError
        If required extraction columns are missing.
    """
    validate_input_columns(df, REQUIRED_FOR_FEATURE_EXTRACTION)
