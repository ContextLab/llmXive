"""
Validation utilities for the perovskite thermal conductivity pipeline.

Provides functions for:
- Variance Inflation Factor (VIF) calculation for multicollinearity detection
- Error handling with structured logging
- Logger setup with consistent formatting
- Causal language scanning to prevent scientific overstatement
"""

import logging
import sys
from typing import List, Optional, Union, Dict, Any
import re
import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor


def setup_logger(name: str, level: Union[int, str] = logging.INFO) -> logging.Logger:
    """
    Configure and return a logger with consistent formatting.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (e.g., logging.INFO, 'DEBUG', 20)

    Returns:
        Configured logger instance
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


def handle_error(message: str, level: str = 'critical') -> None:
    """
    Handle errors with appropriate logging and optional exit.

    Args:
        message: Error message to log
        level: Severity level ('debug', 'info', 'warning', 'error', 'critical')

    Raises:
        SystemExit: For critical errors
    """
    level_map = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }

    log_level = level_map.get(level.lower(), logging.ERROR)
    logger = logging.getLogger(__name__)
    logger.log(log_level, message)

    if level.lower() == 'critical':
        sys.exit(1)


def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for a list of predictor variables.

    VIF quantifies the severity of multicollinearity in a regression model.
    VIF > 5 indicates potential multicollinearity issues.

    Args:
        df: DataFrame containing predictor variables
        predictors: List of column names to calculate VIF for

    Returns:
        DataFrame with columns: ['predictor', 'vif']
    """
    if not all(col in df.columns for col in predictors):
        missing = [col for col in predictors if col not in df.columns]
        raise ValueError(f"Missing predictors in dataframe: {missing}")

    # Ensure we have numeric data
    X = df[predictors].dropna()
    if X.empty:
        raise ValueError("No valid data after dropping NaN values")

    # Add constant for intercept
    X_with_const = sm.add_constant(X)

    vif_data = []
    for i, col in enumerate(X_with_const.columns):
        if col == 'const':
            continue
        try:
            vif = variance_inflation_factor(X_with_const.values, i)
            vif_data.append({'predictor': col, 'vif': vif})
        except Exception as e:
            # Handle cases where VIF cannot be calculated (e.g., constant column)
            vif_data.append({'predictor': col, 'vif': np.nan})

    return pd.DataFrame(vif_data)


def get_high_vif_predictors(df: pd.DataFrame, predictors: List[str], threshold: float = 5.0) -> List[str]:
    """
    Identify predictors with VIF above a specified threshold.

    Args:
        df: DataFrame containing predictor variables
        predictors: List of column names to check
        threshold: VIF threshold (default 5.0)

    Returns:
        List of predictor names with VIF > threshold
    """
    vif_df = calculate_vif(df, predictors)
    high_vif = vif_df[vif_df['vif'] > threshold]
    return high_vif['predictor'].tolist()


def scan_causal_language(text: str) -> Dict[str, Any]:
    """
    Scan text for prohibited causal language that implies causation in correlational research.

    Prohibited keywords: {cause, causes, caused, leads to, led to, driven by,
    effect of, result of, resulting from, induces, triggers}

    Args:
        text: Text content to scan (e.g., markdown report, comments)

    Returns:
        Dictionary with:
            - 'found': Boolean indicating if prohibited language was found
            - 'matches': List of found prohibited phrases and their context
            - 'count': Number of prohibited phrases found
    """
    # Pattern matches whole words to avoid false positives in compound words
    prohibited_patterns = [
        r'\bcause\b', r'\bcauses\b', r'\bcaused\b',
        r'\bleads to\b', r'\bled to\b',
        r'\bdriven by\b',
        r'\beffect of\b',
        r'\bresult of\b', r'\bresulting from\b',
        r'\binduces\b', r'\btriggers\b'
    ]

    matches = []
    text_lower = text.lower()

    for pattern in prohibited_patterns:
        # Find all matches with their positions
        for match in re.finditer(pattern, text_lower, re.IGNORECASE):
            # Get context around the match (50 chars before and after)
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]

            # Highlight the match in context
            matched_text = match.group()
            context_highlighted = (
                context[:match.start() - start] +
                f"***{matched_text}***" +
                context[match.end() - start:]
            )

            matches.append({
                'phrase': matched_text,
                'pattern': pattern,
                'context': context_highlighted,
                'position': match.start()
            })

    return {
        'found': len(matches) > 0,
        'matches': matches,
        'count': len(matches)
    }


def validate_causal_language(text: str, fail_on_found: bool = True) -> bool:
    """
    Validate text against prohibited causal language.

    Args:
        text: Text to validate
        fail_on_found: If True, raise SystemExit when violations are found

    Returns:
        True if no violations found, False otherwise

    Raises:
        SystemExit: If fail_on_found is True and violations are detected
    """
    scan_result = scan_causal_language(text)

    if scan_result['found']:
        logger = logging.getLogger(__name__)
        logger.error("Prohibited causal language detected:")
        for match in scan_result['matches']:
            logger.error(f"  - '{match['phrase']}' found in: {match['context']}")

        if fail_on_found:
            handle_error(
                f"Causal language violation detected: {scan_result['count']} prohibited phrase(s) found. "
                "Please rephrase to use correlational language (e.g., 'associated with', 'correlated with').",
                level='critical'
            )
        return False

    return True


def validate_dataframe_columns(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    Validate that a DataFrame contains all required columns.

    Args:
        df: DataFrame to validate
        required_columns: List of required column names

    Returns:
        True if all columns present, False otherwise
    """
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        logger = logging.getLogger(__name__)
        logger.error(f"Missing required columns: {missing}")
        return False
    return True


def validate_no_nulls(df: pd.DataFrame, columns: Optional[List[str]] = None) -> bool:
    """
    Validate that specified columns contain no null values.

    Args:
        df: DataFrame to validate
        columns: List of columns to check (None checks all columns)

    Returns:
        True if no nulls found, False otherwise
    """
    cols_to_check = columns if columns else df.columns
    null_counts = df[cols_to_check].isnull().sum()
    has_nulls = (null_counts > 0).any()

    if has_nulls:
        logger = logging.getLogger(__name__)
        null_summary = null_counts[null_counts > 0].to_dict()
        logger.error(f"Null values found in columns: {null_summary}")
        return False

    return True


def validate_data_types(df: pd.DataFrame, expected_types: Dict[str, type]) -> bool:
    """
    Validate that columns have expected data types.

    Args:
        df: DataFrame to validate
        expected_types: Dictionary mapping column names to expected types

    Returns:
        True if all types match, False otherwise
    """
    for col, expected_type in expected_types.items():
        if col not in df.columns:
            logger = logging.getLogger(__name__)
            logger.error(f"Column '{col}' not found in DataFrame")
            return False

        # Check if dtype is compatible (e.g., int64 is compatible with int)
        actual_dtype = df[col].dtype
        if not np.issubdtype(actual_dtype, expected_type):
            logger = logging.getLogger(__name__)
            logger.error(
                f"Column '{col}' has dtype {actual_dtype}, expected {expected_type}"
            )
            return False

    return True
