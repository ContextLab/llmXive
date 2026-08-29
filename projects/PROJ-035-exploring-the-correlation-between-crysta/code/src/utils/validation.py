"""
Validation utilities for the perovskite thermal conductivity pipeline.

Implements:
- VIF calculation and high-VIF predictor exclusion (FR-008)
- Causal language scanning and validation (FR-007)
- DataFrame column and null validation
"""

import logging
import sys
from typing import List, Optional, Union, Dict, Any
import re
import numpy as np
import pandas as pd

try:
    from statsmodels.stats.outliers_influence import variance_inflation_factor
except ImportError:
    variance_inflation_factor = None
    logging.warning("statsmodels not available; VIF calculations will fail.")

# Prohibited causal language keywords (FR-007)
PROHIBITED_CAUSAL_KEYWORDS = {
    "cause", "causes", "caused", "causing",
    "leads to", "lead to", "led to",
    "driven by", "driving",
    "effect of", "effects of",
    "result of", "resulting from",
    "determines", "determined by",
    "influences"  # Added to catch subtle causal claims
}

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger with consistent formatting.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (INFO, DEBUG, etc.)
        
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

def handle_error(message: str, level: str = "critical") -> None:
    """
    Handle errors based on severity level.
    
    Args:
        message: Error message to log
        level: One of 'critical', 'error', 'warning', 'info'
        
    Raises:
        RuntimeError: For critical and error levels
    """
    logger = logging.getLogger(__name__)
    
    level_map = {
        "critical": logger.critical,
        "error": logger.error,
        "warning": logger.warning,
        "info": logger.info
    }
    
    log_func = level_map.get(level.lower(), logger.error)
    log_func(message)
    
    if level.lower() in ("critical", "error"):
        raise RuntimeError(message)

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> pd.Series:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.
    
    VIF measures multicollinearity. A VIF > 5 indicates high collinearity
    and suggests the predictor should be excluded from regression models.
    
    Args:
        df: DataFrame containing predictor columns
        predictors: List of column names to calculate VIF for
        
    Returns:
        Series with VIF values for each predictor
        
    Raises:
        ImportError: If statsmodels is not available
        ValueError: If predictors are not in DataFrame or contain non-numeric data
    """
    if variance_inflation_factor is None:
        raise ImportError(
            "statsmodels is required for VIF calculation. "
            "Install with: pip install statsmodels"
        )
    
    # Validate inputs
    missing_cols = [col for col in predictors if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Predictors not found in DataFrame: {missing_cols}")
    
    # Check for numeric data
    X = df[predictors].copy()
    if not np.issubdtype(X.values.dtype, np.number):
        raise ValueError("All predictor columns must be numeric for VIF calculation")
    
    # Handle constant columns (VIF undefined)
    if X.std().min() == 0:
        raise ValueError("Predictor columns must have non-zero variance")
    
    # Calculate VIF
    # Add intercept column for VIF calculation
    X_with_intercept = pd.concat([pd.Series(np.ones(len(X)), name='intercept'), X], axis=1)
    
    vif_series = pd.Series(
        [variance_inflation_factor(X_with_intercept.values, i) 
         for i in range(len(X_with_intercept.columns))],
        index=X_with_intercept.columns
    )
    
    # Remove intercept VIF
    vif_series = vif_series.drop('intercept')
    
    return vif_series

def get_high_vif_predictors(
    df: pd.DataFrame, 
    predictors: List[str], 
    threshold: float = 5.0
) -> List[str]:
    """
    Identify predictors with VIF above the specified threshold.
    
    Args:
        df: DataFrame containing predictor columns
        predictors: List of candidate predictor column names
        threshold: VIF threshold for exclusion (default: 5.0)
        
    Returns:
        List of predictor names with VIF > threshold
    """
    vif_series = calculate_vif(df, predictors)
    high_vif = vif_series[vif_series > threshold].index.tolist()
    return high_vif

def scan_causal_language(text: str) -> List[Dict[str, Any]]:
    """
    Scan text for prohibited causal language keywords.
    
    This function implements Constitution VII compliance by detecting
    causal claims that should not appear in research descriptions.
    
    Args:
        text: Text to scan for causal language
        
    Returns:
        List of dictionaries with match details:
        - keyword: The matched prohibited word/phrase
        - position: Start position in text
        - context: Surrounding text (50 chars before/after)
    """
    if not isinstance(text, str):
        return []
    
    text_lower = text.lower()
    matches = []
    
    for keyword in PROHIBITED_CAUSAL_KEYWORDS:
        # Use word boundaries for single words, exact match for phrases
        if ' ' in keyword:
            # Phrase matching
            pattern = re.escape(keyword)
            for match in re.finditer(pattern, text_lower):
                start = match.start()
                end = match.end()
                context_start = max(0, start - 50)
                context_end = min(len(text), end + 50)
                context = text[context_start:context_end]
                
                matches.append({
                    "keyword": keyword,
                    "position": start,
                    "context": context
                })
        else:
            # Word boundary matching for single words
            pattern = r'\b' + re.escape(keyword) + r'\b'
            for match in re.finditer(pattern, text_lower):
                start = match.start()
                end = match.end()
                context_start = max(0, start - 50)
                context_end = min(len(text), end + 50)
                context = text[context_start:context_end]
                
                matches.append({
                    "keyword": keyword,
                    "position": start,
                    "context": context
                })
    
    return matches

def validate_causal_language(text: str, raise_on_violation: bool = True) -> bool:
    """
    Validate text contains no prohibited causal language.
    
    Args:
        text: Text to validate
        raise_on_violation: If True, raise RuntimeError on violation
        
    Returns:
        True if text passes validation, False otherwise
        
    Raises:
        RuntimeError: If violations found and raise_on_violation is True
    """
    matches = scan_causal_language(text)
    
    if matches:
        violation_msg = (
            f"Found {len(matches)} prohibited causal language instances:\n"
        )
        for i, match in enumerate(matches, 1):
            violation_msg += (
                f"  {i}. Keyword: '{match['keyword']}' at position {match['position']}\n"
                f"     Context: ...{match['context']}...\n"
            )
        
        if raise_on_violation:
            raise RuntimeError(violation_msg)
        else:
            logging.warning(violation_msg)
            return False
    
    return True

def validate_dataframe_columns(
    df: pd.DataFrame, 
    required_columns: List[str], 
    optional_columns: Optional[List[str]] = None
) -> bool:
    """
    Validate that a DataFrame contains required columns.
    
    Args:
        df: DataFrame to validate
        required_columns: List of column names that must exist
        optional_columns: List of column names that may exist
        
    Returns:
        True if validation passes
        
    Raises:
        ValueError: If required columns are missing
    """
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    if optional_columns:
        extra = [col for col in optional_columns if col not in df.columns]
        if extra:
            logging.debug(f"Optional columns not found: {extra}")
    
    return True

def validate_no_nulls(df: pd.DataFrame, columns: Optional[List[str]] = None) -> bool:
    """
    Validate that specified columns contain no null values.
    
    Args:
        df: DataFrame to validate
        columns: List of columns to check. If None, checks all columns.
        
    Returns:
        True if no nulls found
        
    Raises:
        ValueError: If nulls are found in checked columns
    """
    cols_to_check = columns if columns else df.columns.tolist()
    
    for col in cols_to_check:
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame")
        
        null_count = df[col].isnull().sum()
        if null_count > 0:
            raise ValueError(f"Column '{col}' contains {null_count} null values")
    
    return True

def validate_data_types(
    df: pd.DataFrame, 
    expected_types: Dict[str, str]
) -> bool:
    """
    Validate that columns have expected data types.
    
    Args:
        df: DataFrame to validate
        expected_types: Dict mapping column names to expected dtype strings
            (e.g., {'thermal_conductivity': 'float64', 'structure_id': 'object'})
        
    Returns:
        True if all types match
        
    Raises:
        ValueError: If types don't match
    """
    for col, expected_type in expected_types.items():
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame")
        
        actual_type = str(df[col].dtype)
        if actual_type != expected_type:
            raise ValueError(
                f"Column '{col}' has type '{actual_type}', expected '{expected_type}'"
            )
    
    return True