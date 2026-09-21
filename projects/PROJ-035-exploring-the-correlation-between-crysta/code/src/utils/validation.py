"""
Validation utilities for the perovskite thermal conductivity pipeline.

This module provides functions for:
- Variance Inflation Factor (VIF) calculation
- Causal language scanning
- Data validation utilities
- Logging setup
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
    Setup a logger with the given name and level.
    
    Args:
        name: Logger name
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def handle_error(error: Exception, logger: Optional[logging.Logger] = None) -> None:
    """
    Handle and log an error, then re-raise it.
    
    Args:
        error: The exception to handle
        logger: Optional logger instance
        
    Raises:
        The original exception
    """
    if logger:
        logger.error(f"Error occurred: {str(error)}")
    raise error


def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor variable.
    
    VIF measures multicollinearity in regression analysis. A VIF > 5 indicates
    high multicollinearity that may require addressing.
    
    Args:
        df: DataFrame containing the predictor variables
        predictors: List of column names to calculate VIF for
        
    Returns:
        Dictionary mapping predictor names to their VIF values
        
    Raises:
        ValueError: If any predictor column is not found in the DataFrame
        ValueError: If predictors list is empty
    """
    if not predictors:
        raise ValueError("Predictors list cannot be empty")
    
    # Validate columns exist
    missing_cols = [col for col in predictors if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Columns not found in DataFrame: {missing_cols}")
    
    X = df[predictors].dropna()
    
    if X.empty:
        raise ValueError("No valid data after dropping NaN values")
    
    vif_results = {}
    for i, col in enumerate(X.columns):
        vif = variance_inflation_factor(X.values, i)
        vif_results[col] = float(vif)
    
    return vif_results


def get_high_vif_predictors(vif_results: Dict[str, float], threshold: float = 5.0) -> List[str]:
    """
    Identify predictors with VIF exceeding the threshold.
    
    Args:
        vif_results: Dictionary of VIF values from calculate_vif
        threshold: VIF threshold (default: 5.0)
        
    Returns:
        List of predictor names with VIF > threshold
    """
    return [col for col, vif in vif_results.items() if vif > threshold]


def scan_causal_language(text: str) -> Dict[str, Any]:
    """
    Scan text for prohibited causal language keywords.
    
    This function checks for causal language that violates Constitution VII
    and FR-007, which prohibit claiming causal relationships without
    experimental verification.
    
    Prohibited keywords: cause, leads to, driven by, effect of, result of
    
    Args:
        text: Text to scan for causal language
        
    Returns:
        Dictionary with 'found' (bool), 'matches' (list of found keywords),
        and 'positions' (list of tuples with keyword and position)
        
    Raises:
        ValueError: If prohibited causal language is found
        
    Examples:
        >>> scan_causal_language("The temperature leads to changes")
        Traceback (most recent call last):
            ValueError: Prohibited causal language found: leads to
    """
    prohibited_keywords = [
        r'\bcause\b',
        r'\bleads to\b',
        r'\bdriven by\b',
        r'\beffect of\b',
        r'\bresult of\b'
    ]
    
    text_lower = text.lower()
    found_matches = []
    positions = []
    
    for pattern in prohibited_keywords:
        matches = list(re.finditer(pattern, text_lower))
        for match in matches:
            keyword = match.group()
            found_matches.append(keyword)
            positions.append((keyword, match.start()))
    
    if found_matches:
        unique_keywords = list(set(found_matches))
        raise ValueError(
            f"Prohibited causal language found: {', '.join(unique_keywords)}"
        )
    
    return {
        'found': False,
        'matches': [],
        'positions': []
    }


def validate_causal_language(text: str, logger: Optional[logging.Logger] = None) -> bool:
    """
    Validate text for causal language violations.
    
    This is a wrapper around scan_causal_language that logs results
    and returns a boolean instead of raising.
    
    Args:
        text: Text to validate
        logger: Optional logger for logging results
        
    Returns:
        True if no violations found, False otherwise
    """
    try:
        result = scan_causal_language(text)
        if logger:
            logger.info("Causal language check passed")
        return True
    except ValueError as e:
        if logger:
            logger.error(f"Causal language violation: {str(e)}")
        return False


def validate_dataframe_columns(df: pd.DataFrame, required_columns: List[str]) -> List[str]:
    """
    Validate that a DataFrame contains all required columns.
    
    Args:
        df: DataFrame to validate
        required_columns: List of required column names
        
    Returns:
        List of missing columns (empty if all present)
    """
    missing = [col for col in required_columns if col not in df.columns]
    return missing


def validate_no_nulls(df: pd.DataFrame, columns: Optional[List[str]] = None) -> Dict[str, int]:
    """
    Check for null values in specified columns.
    
    Args:
        df: DataFrame to check
        columns: List of columns to check (None checks all columns)
        
    Returns:
        Dictionary mapping column names to null count
    """
    if columns is None:
        columns = df.columns.tolist()
    
    null_counts = {}
    for col in columns:
        if col in df.columns:
            null_counts[col] = int(df[col].isna().sum())
        else:
            null_counts[col] = -1  # Column not found
    
    return null_counts


def validate_data_types(df: pd.DataFrame, expected_types: Dict[str, str]) -> List[str]:
    """
    Validate data types of columns.
    
    Args:
        df: DataFrame to validate
        expected_types: Dictionary mapping column names to expected dtype strings
        
    Returns:
        List of columns with incorrect types
    """
    incorrect = []
    for col, expected in expected_types.items():
        if col in df.columns:
            actual = str(df[col].dtype)
            if expected not in actual:
                incorrect.append(col)
    return incorrect