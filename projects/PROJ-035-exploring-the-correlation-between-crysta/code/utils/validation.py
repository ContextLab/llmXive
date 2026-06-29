"""
Validation utilities for the perovskite thermal conductivity analysis pipeline.

This module provides core validation functions used across the pipeline:
- Variance Inflation Factor (VIF) calculation for multicollinearity detection
- Error handling with configurable severity levels
- Logger setup with consistent formatting
"""
import logging
import sys
from typing import List, Optional, Union

import numpy as np
import pandas as pd
from statsmodels.stats.outliers_influence import variance_inflation_factor


def setup_logger(
    name: str,
    level: Union[str, int] = logging.INFO
) -> logging.Logger:
    """
    Setup a logger with the given name and level.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        level: Logging level (e.g., 'INFO', 'DEBUG', logging.INFO)
    
    Returns:
        Configured Logger instance
    
    Examples:
        >>> logger = setup_logger(__name__, 'DEBUG')
        >>> logger.info('Logger setup complete')
    """
    # Convert string level to int if needed
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    # Get or create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger
    
    # Create console handler with formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger


def handle_error(
    message: str,
    level: str = 'error'
) -> None:
    """
    Handle errors with configurable severity level.
    
    Args:
        message: Error message to log/raise
        level: Severity level ('debug', 'info', 'warning', 'error', 'critical')
    
    Raises:
        ValueError: For 'error' or 'critical' levels
        Warning: For 'warning' level
    
    Examples:
        >>> handle_error('Missing required field', 'warning')
        >>> handle_error('Critical failure', 'critical')  # Raises ValueError
    """
    level = level.lower()
    valid_levels = {'debug', 'info', 'warning', 'error', 'critical'}
    
    if level not in valid_levels:
        raise ValueError(f"Invalid level: {level}. Must be one of {valid_levels}")
    
    if level in ('debug', 'info'):
        logger = setup_logger(__name__, level)
        getattr(logger, level)(message)
    elif level == 'warning':
        import warnings
        warnings.warn(message, UserWarning)
    elif level == 'error':
        raise ValueError(message)
    elif level == 'critical':
        raise RuntimeError(message)


def calculate_vif(
    df: pd.DataFrame,
    predictors: List[str]
) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for specified predictors.
    
    VIF measures multicollinearity in regression models. A VIF > 5 typically
    indicates problematic multicollinearity that may require feature removal.
    
    Args:
        df: DataFrame containing all predictor variables
        predictors: List of column names to calculate VIF for
    
    Returns:
        DataFrame with columns ['predictor', 'vif'] sorted by VIF descending
    
    Raises:
        ValueError: If predictors contain non-existent columns or insufficient data
    
    Examples:
        >>> df = pd.DataFrame({'A': [1,2,3,4,5], 'B': [2,4,6,8,10], 'C': [1,3,5,7,9]})
        >>> vif_df = calculate_vif(df, ['A', 'B', 'C'])
        >>> assert 'vif' in vif_df.columns
    """
    if not predictors:
        handle_error("No predictors provided for VIF calculation", 'error')
    
    # Validate predictors exist in dataframe
    missing = [p for p in predictors if p not in df.columns]
    if missing:
        handle_error(
            f"Predictors not found in dataframe: {missing}",
            'error'
        )
    
    # Check for constant or near-constant columns
    for p in predictors:
        if df[p].std() < 1e-10:
            handle_error(
                f"Predictor '{p}' has zero or near-zero variance",
                'error'
            )
    
    # Extract predictor matrix
    X = df[predictors].values
    
    # Add constant term for intercept
    X_with_const = np.column_stack([np.ones(X.shape[0]), X])
    
    # Calculate VIF for each predictor (excluding constant term)
    vif_data = []
    for i, predictor in enumerate(predictors):
        try:
            vif = variance_inflation_factor(X_with_const, i + 1)
            vif_data.append({
                'predictor': predictor,
                'vif': vif
            })
        except Exception as e:
            handle_error(
                f"Failed to calculate VIF for '{predictor}': {str(e)}",
                'error'
            )
    
    vif_df = pd.DataFrame(vif_data)
    vif_df = vif_df.sort_values('vif', ascending=False).reset_index(drop=True)
    
    return vif_df


def get_high_vif_predictors(
    vif_df: pd.DataFrame,
    threshold: float = 5.0
) -> List[str]:
    """
    Get list of predictors with VIF above threshold.
    
    Args:
        vif_df: VIF DataFrame from calculate_vif()
        threshold: VIF threshold (default 5.0)
    
    Returns:
        List of predictor names with VIF > threshold
    
    Examples:
        >>> vif_df = pd.DataFrame({'predictor': ['A', 'B'], 'vif': [2.0, 8.0]})
        >>> high_vif = get_high_vif_predictors(vif_df, threshold=5.0)
        >>> assert high_vif == ['B']
    """
    return vif_df[vif_df['vif'] > threshold]['predictor'].tolist()
