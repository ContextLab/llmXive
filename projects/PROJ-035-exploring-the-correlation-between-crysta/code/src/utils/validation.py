"""
Validation utilities for the perovskite thermal conductivity pipeline.

This module provides functions for:
- Variance Inflation Factor (VIF) calculation for multicollinearity detection
- Causal language scanning to prevent overinterpretation
- Logger setup with consistent formatting
"""
import logging
import sys
from typing import List, Optional, Union, Dict, Any
import re
import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Prohibited causal keywords that indicate overinterpretation
PROHIBITED_CAUSAL_KEYWORDS = {
    "cause", "causes", "causing",
    "leads to", "lead to", "led to",
    "driven by", "drives", "driving",
    "effect of", "effects of",
    "result of", "results in", "resulting in",
    "determines", "determined by",
    "causally", "causation"
}

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with consistent formatting.
    
    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    
    Raises:
        None
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding duplicate handlers if logger already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger

def handle_error(error: Exception, context: str = "") -> None:
    """
    Handle errors with consistent logging and exit behavior.
    
    Args:
        error: The exception to handle
        context: Optional context string to include in error message
    
    Returns:
        None (exits program with code 1)
    """
    logger = setup_logger(__name__)
    error_msg = str(error)
    if context:
        error_msg = f"{context}: {error_msg}"
    
    logger.error(f"Error occurred: {error_msg}")
    sys.exit(1)

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor variable.
    
    VIF measures how much the variance of a regression coefficient is 
    inflated due to multicollinearity with other predictors.
    
    Args:
        df: DataFrame containing predictor variables
        predictors: List of column names to calculate VIF for
    
    Returns:
        DataFrame with columns: 'predictor', 'VIF'
        VIF > 5 indicates problematic multicollinearity
    
    Raises:
        ValueError: If any predictor column is not in DataFrame
        ValueError: If any predictor contains non-numeric data
        ValueError: If DataFrame is empty
    """
    if not predictors:
        raise ValueError("Predictors list cannot be empty")
    
    # Validate columns exist
    missing_cols = [col for col in predictors if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Predictors not found in DataFrame: {missing_cols}")
    
    # Extract predictor data
    X = df[predictors].copy()
    
    # Check for numeric data
    if not np.issubdtype(X.values.dtype, np.number):
        # Try to convert, but fail if not possible
        try:
            X = X.apply(pd.to_numeric)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Predictors must contain numeric data: {str(e)}")
    
    # Check for empty DataFrame
    if X.empty:
        raise ValueError("DataFrame is empty")
    
    # Check for constant columns (VIF undefined)
    constant_cols = [col for col in X.columns if X[col].std() == 0]
    if constant_cols:
        raise ValueError(f"Constant columns detected (VIF undefined): {constant_cols}")
    
    # Calculate VIF for each predictor
    vif_data = []
    for i, col in enumerate(predictors):
        # Create design matrix without the current column
        X_design = X.drop(columns=[col])
        
        # Add intercept column
        X_design_with_intercept = X_design.copy()
        X_design_with_intercept['intercept'] = 1.0
        
        try:
            vif = variance_inflation_factor(
                X_design_with_intercept.values, 
                X_design_with_intercept.columns.get_loc(col) if col in X_design_with_intercept.columns else 0
            )
        except Exception as e:
            # Handle cases where VIF cannot be calculated
            vif = float('inf')
        
        vif_data.append({'predictor': col, 'VIF': vif})
    
    return pd.DataFrame(vif_data)

def get_high_vif_predictors(vif_df: pd.DataFrame, threshold: float = 5.0) -> List[str]:
    """
    Identify predictors with VIF above a specified threshold.
    
    Args:
        vif_df: DataFrame from calculate_vif() with 'predictor' and 'VIF' columns
        threshold: VIF threshold above which predictors are considered problematic (default: 5.0)
    
    Returns:
        List of predictor names with VIF > threshold
    
    Raises:
        ValueError: If input DataFrame lacks required columns
    """
    if 'predictor' not in vif_df.columns or 'VIF' not in vif_df.columns:
        raise ValueError("Input DataFrame must contain 'predictor' and 'VIF' columns")
    
    high_vif = vif_df[vif_df['VIF'] > threshold]['predictor'].tolist()
    return high_vif

def scan_causal_language(text: str) -> Dict[str, Any]:
    """
    Scan text for prohibited causal language that indicates overinterpretation.
    
    This function checks for keywords and phrases that suggest causal relationships
    where only correlation has been demonstrated.
    
    Args:
        text: Text string to scan for causal language
    
    Returns:
        Dictionary with:
            - 'found': Boolean indicating if prohibited language was found
            - 'matches': List of tuples (matched_text, position)
            - 'count': Number of matches found
    
    Raises:
        TypeError: If input is not a string
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    
    text_lower = text.lower()
    matches = []
    
    for keyword in PROHIBITED_CAUSAL_KEYWORDS:
        # Search for the keyword in the text
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        for match in pattern.finditer(text):
            matches.append({
                'keyword': keyword,
                'position': match.start(),
                'context': text[max(0, match.start()-20):min(len(text), match.end()+20)]
            })
    
    return {
        'found': len(matches) > 0,
        'matches': matches,
        'count': len(matches)
    }

def validate_causal_language(text: str, fail_on_violation: bool = True) -> bool:
    """
    Validate text for prohibited causal language.
    
    Args:
        text: Text string to validate
        fail_on_violation: If True, raise SystemExit on violation (default: True)
    
    Returns:
        True if no violations found, False otherwise
    
    Raises:
        SystemExit: If fail_on_violation is True and violations are found
    """
    result = scan_causal_language(text)
    
    if result['found']:
        logger = setup_logger(__name__)
        logger.warning(f"Found {result['count']} instances of prohibited causal language:")
        for match in result['matches']:
            logger.warning(f"  - '{match['keyword']}' at position {match['position']}: ...{match['context']}...")
        
        if fail_on_violation:
            handle_error(
                ValueError("Prohibited causal language detected in text"),
                "Causal language validation failed"
            )
        return False
    
    return True

def validate_dataframe_columns(df: pd.DataFrame, required_columns: List[str]) -> None:
    """
    Validate that a DataFrame contains all required columns.
    
    Args:
        df: DataFrame to validate
        required_columns: List of column names that must be present
    
    Raises:
        ValueError: If any required columns are missing
    """
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

def validate_no_nulls(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, int]:
    """
    Validate that specified columns contain no null values.
    
    Args:
        df: DataFrame to validate
        columns: List of columns to check. If None, checks all columns.
    
    Returns:
        Dictionary mapping column names to null counts (only columns with nulls)
    
    Raises:
        ValueError: If any checked column contains null values
    """
    if columns is None:
        columns = df.columns.tolist()
    
    null_counts = {}
    for col in columns:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame")
        
        count = df[col].isnull().sum()
        if count > 0:
            null_counts[col] = count
    
    if null_counts:
        error_msg = f"Null values found in columns: {null_counts}"
        raise ValueError(error_msg)
    
    return null_counts

def validate_data_types(df: pd.DataFrame, column_types: Dict[str, type]) -> None:
    """
    Validate that columns have expected data types.
    
    Args:
        df: DataFrame to validate
        column_types: Dictionary mapping column names to expected types
    
    Raises:
        ValueError: If any column has incorrect data type
    """
    for col, expected_type in column_types.items():
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame")
        
        actual_type = df[col].dtype
        # Handle pandas extension dtypes
        if not np.issubdtype(actual_type, np.number) and expected_type in [int, float, np.number]:
            # Check if it can be converted to numeric
            try:
                pd.to_numeric(df[col])
            except (ValueError, TypeError):
                raise ValueError(
                    f"Column '{col}' has incorrect type: {actual_type}, "
                    f"expected numeric type"
                )
        elif not isinstance(df[col].iloc[0], expected_type) if len(df) > 0 else True:
            # For non-numeric types, check the actual type
            if len(df) > 0 and not isinstance(df[col].iloc[0], expected_type):
                raise ValueError(
                    f"Column '{col}' has incorrect type: {type(df[col].iloc[0])}, "
                    f"expected {expected_type}"
                )