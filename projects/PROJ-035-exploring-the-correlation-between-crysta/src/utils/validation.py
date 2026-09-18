"""
Base validation utilities for the perovskite thermal conductivity research pipeline.

This module provides core validation functions for:
1. Variance Inflation Factor (VIF) calculation for multicollinearity detection
2. Causal language scanning to prevent causal claims in correlation studies
3. Logger setup for consistent logging across the pipeline
"""

import logging
import sys
from typing import List, Optional, Union, Dict, Any
import re
import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Create and configure a logger with consistent formatting.

    Input contracts:
      - name: str - The name of the logger (typically __name__ of the calling module)
      - level: int - Logging level (e.g., logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR)
    
    Output contracts:
      - Returns a configured logging.Logger instance
      - The logger outputs to stdout with a standardized format
      - The logger is configured with the specified level
    
    Behavior:
      - Sets up a formatter with timestamp, level, name, and message
      - Creates a StreamHandler for stdout
      - Adds the handler to the logger
      - Sets the logger's level
      - Prevents duplicate handlers if called multiple times with same name
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        handler.setLevel(level)
        logger.addHandler(handler)
    
    return logger


def handle_error(error: Exception, logger: Optional[logging.Logger] = None, message: Optional[str] = None) -> None:
    """
    Handle and log errors with optional custom message.
    
    Input contracts:
      - error: Exception - The exception instance to handle
      - logger: Optional[logging.Logger] - Logger instance for error logging. If None, uses default logger.
      - message: Optional[str] - Custom error message. If None, uses exception string representation.
    
    Output contracts:
      - Logs the error with appropriate context
      - Re-raises the exception after logging
    
    Behavior:
      - Logs error message at ERROR level
      - Includes exception type and message
      - Re-raises the original exception to propagate the error
    """
    log_msg = message if message else str(error)
    log_full = f"{log_msg}: {type(error).__name__}: {error}"
    
    if logger:
        logger.error(log_full)
    else:
        default_logger = setup_logger(__name__, logging.ERROR)
        default_logger.error(log_full)
    
    raise error


def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor variable.
    
    VIF measures multicollinearity in regression analysis. A VIF > 5 indicates
    high multicollinearity, suggesting the variable should be considered for removal.
    
    Input contracts:
      - df: pd.DataFrame - DataFrame containing all predictor variables
      - predictors: List[str] - List of column names to calculate VIF for.
        All columns must exist in df and contain numeric data.
    
    Output contracts:
      - Returns a dictionary mapping each predictor name to its VIF value (float)
      - VIF values are >= 1.0
      - The dictionary contains exactly the predictors listed in input
    
    Behavior:
      - Adds a constant column (intercept) to the design matrix
      - Calculates VIF for each predictor using statsmodels
      - Returns VIF values for all requested predictors
    
    Raises:
      - ValueError: If any predictor column is missing from df
      - ValueError: If any predictor column contains non-numeric data
      - ValueError: If df is empty or predictors list is empty
    """
    if not predictors:
        raise ValueError("Predictors list cannot be empty")
    
    if df.empty:
        raise ValueError("DataFrame cannot be empty")
    
    # Validate all predictors exist
    missing = [p for p in predictors if p not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in DataFrame: {missing}")
    
    # Validate numeric data
    for col in predictors:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValueError(f"Column '{col}' must contain numeric data")
    
    # Handle missing values by dropping rows
    df_clean = df[predictors].dropna()
    
    if df_clean.empty:
        raise ValueError("No valid data remaining after removing NaN values")
    
    # Add constant for intercept
    X = df_clean.copy()
    X['intercept'] = 1.0
    
    vif_results = {}
    for col in predictors:
        # VIF for a variable is 1 / (1 - R^2) where R^2 is from regressing
        # this variable against all others
        try:
            vif = variance_inflation_factor(X.values, list(X.columns).index(col))
            vif_results[col] = float(vif)
        except Exception as e:
            raise ValueError(f"Error calculating VIF for '{col}': {e}")
    
    return vif_results


def get_high_vif_predictors(vif_dict: Dict[str, float], threshold: float = 5.0) -> List[str]:
    """
    Identify predictors with VIF above a specified threshold.
    
    Input contracts:
      - vif_dict: Dict[str, float] - Dictionary of predictor names to VIF values
        (typically from calculate_vif)
      - threshold: float - VIF threshold for flagging high multicollinearity.
        Default is 5.0 (commonly used threshold).
    
    Output contracts:
      - Returns a list of predictor names with VIF > threshold
      - List is sorted by VIF value in descending order
      - Empty list if no predictors exceed threshold
    
    Behavior:
      - Filters predictors where VIF > threshold
      - Sorts by VIF value descending (highest multicollinearity first)
    """
    high_vif = {k: v for k, v in vif_dict.items() if v > threshold}
    return sorted(high_vif.keys(), key=lambda x: high_vif[x], reverse=True)


def scan_causal_language(text: str) -> Dict[str, Any]:
    """
    Scan text for prohibited causal language that violates correlation-only policy.
    
    This function enforces Constitution VII and FR-007 by detecting language that
    implies causation in a correlation study.
    
    Input contracts:
      - text: str - Text content to scan for causal language
    
    Output contracts:
      - Returns a dictionary with:
        - 'found': bool - True if prohibited language detected
        - 'matches': List[str] - List of prohibited phrases found
        - 'positions': List[Dict] - List of {phrase, start, end} for each match
        - 'severity': str - 'high' if any matches found, 'none' otherwise
    
    Behavior:
      - Searches for prohibited keywords: cause, leads to, driven by, effect of, result of
      - Case-insensitive matching
      - Returns detailed position information for each match
      - Does not modify the input text
    
    Prohibited keywords (case-insensitive):
      - "cause", "causes", "causing"
      - "leads to", "lead to", "led to"
      - "driven by", "drive by"
      - "effect of", "affect of"
      - "result of", "resulting from"
    """
    prohibited_patterns = [
        r'\bcause\b', r'\bcauses\b', r'\bcausing\b',
        r'\bleads to\b', r'\blead to\b', r'\bled to\b',
        r'\bdriven by\b', r'\bdrive by\b',
        r'\beffect of\b', r'\baffect of\b',
        r'\bresult of\b', r'\bresulting from\b'
    ]
    
    text_lower = text.lower()
    matches = []
    positions = []
    
    for pattern in prohibited_patterns:
        for match in re.finditer(pattern, text_lower):
            original_text = text[match.start():match.end()]
            matches.append(original_text)
            positions.append({
                'phrase': original_text,
                'start': match.start(),
                'end': match.end()
            })
    
    return {
        'found': len(matches) > 0,
        'matches': matches,
        'positions': positions,
        'severity': 'high' if matches else 'none'
    }


def validate_causal_language(text: str, logger: Optional[logging.Logger] = None) -> bool:
    """
    Validate text for prohibited causal language and raise error if found.
    
    Input contracts:
      - text: str - Text to validate
      - logger: Optional[logging.Logger] - Logger for error reporting
    
    Output contracts:
      - Returns True if text passes validation (no prohibited language)
      - Raises ValueError if prohibited causal language is detected
    
    Behavior:
      - Calls scan_causal_language
      - If violations found, logs error and raises ValueError with details
      - Returns True if no violations
    """
    scan_result = scan_causal_language(text)
    
    if scan_result['found']:
        error_msg = f"Prohibited causal language detected: {scan_result['matches']}"
        if logger:
            logger.error(error_msg)
        else:
            default_logger = setup_logger(__name__, logging.ERROR)
            default_logger.error(error_msg)
        raise ValueError(error_msg)
    
    return True


def validate_dataframe_columns(df: pd.DataFrame, required_columns: List[str]) -> List[str]:
    """
    Validate that a DataFrame contains all required columns.
    
    Input contracts:
      - df: pd.DataFrame - DataFrame to validate
      - required_columns: List[str] - List of column names that must exist
    
    Output contracts:
      - Returns a list of missing column names
      - Empty list if all required columns are present
    
    Behavior:
      - Checks each required column against df.columns
      - Returns list of columns not found in df
    """
    return [col for col in required_columns if col not in df.columns]


def validate_no_nulls(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, int]:
    """
    Check for null values in specified columns of a DataFrame.
    
    Input contracts:
      - df: pd.DataFrame - DataFrame to validate
      - columns: Optional[List[str]] - Specific columns to check. If None, checks all columns.
    
    Output contracts:
      - Returns a dictionary mapping column names to null count
      - Only includes columns with null count > 0
      - Empty dictionary if no nulls found in checked columns
    
    Behavior:
      - If columns specified, only checks those columns
      - If columns not specified, checks all columns
      - Counts null (NaN) values per column
    """
    cols_to_check = columns if columns else df.columns
    null_counts = df[cols_to_check].isna().sum()
    return {col: int(count) for col, count in null_counts.items() if count > 0}
