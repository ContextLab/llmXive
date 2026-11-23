"""
Statistical helper functions for the statistical bias analysis pipeline.

This module provides utilities for handling interval-censored data,
converting inequality strings to bounds, and fitting Tobit models
for effect size analysis.
"""

import re
from typing import Tuple, Optional

import numpy as np
import statsmodels.api as sm
from statsmodels.duration.hazard_regression import TobitReg


def convert_inequality_to_bounds(inequality_str: str) -> Tuple[float, float, str]:
    """
    Parses p-value inequality strings into numerical bounds and type.

    Handles common formats found in academic papers:
    - "p < 0.05" -> (0.0, 0.05, "inequality")
    - "p <= 0.05" -> (0.0, 0.05, "inequality")
    - "p > 0.05" -> (0.05, 1.0, "inequality")
    - "p >= 0.05" -> (0.05, 1.0, "inequality")
    - "p < 0.001" -> (0.0, 0.001, "inequality")
    - "p = 0.03" -> (0.03, 0.03, "exact")
    - "p=0.03" -> (0.03, 0.03, "exact")
    - "0.03" -> (0.03, 0.03, "exact")

    Args:
        inequality_str: String containing the p-value inequality or value.

    Returns:
        Tuple of (lower_bound, upper_bound, type):
            - lower_bound: float, the lower numerical bound
            - upper_bound: float, the upper numerical bound
            - type: str, either "inequality" or "exact"

    Raises:
        ValueError: If the string cannot be parsed into a valid p-value range.
    """
    if not isinstance(inequality_str, str):
        raise ValueError(f"Input must be a string, got {type(inequality_str)}")

    # Clean the string: remove whitespace and convert to lowercase
    clean_str = inequality_str.strip().lower()

    # Remove common prefixes like "p =", "p=", "p-value =", etc.
    clean_str = re.sub(r'^p\s*=?\s*', '', clean_str)
    clean_str = re.sub(r'^p-value\s*=?\s*', '', clean_str)

    # Handle exact values (e.g., "0.03", "0.001")
    exact_pattern = r'^(\d+\.?\d*)$'
    exact_match = re.match(exact_pattern, clean_str)
    if exact_match:
        val = float(exact_match.group(1))
        if not 0.0 <= val <= 1.0:
            raise ValueError(f"P-value {val} is outside valid range [0, 1]")
        return (val, val, "exact")

    # Handle inequality patterns
    # Patterns: <, <=, >, >=
    inequality_pattern = r'^(<|<=|>|>=)\s*(\d+\.?\d*)$'
    match = re.match(inequality_pattern, clean_str)

    if not match:
        raise ValueError(f"Cannot parse p-value inequality: '{inequality_str}'")

    operator = match.group(1)
    value = float(match.group(2))

    if not 0.0 <= value <= 1.0:
        raise ValueError(f"P-value {value} is outside valid range [0, 1]")

    if operator in ['<', '<=']:
        # p < 0.05 means the true value is in (0, 0.05)
        return (0.0, value, "inequality")
    elif operator in ['>', '>=']:
        # p > 0.05 means the true value is in (0.05, 1.0)
        return (value, 1.0, "inequality")
    else:
        raise ValueError(f"Unsupported operator: {operator}")


def fit_tobit_model(
    X: np.ndarray,
    y: np.ndarray,
    lower: float = 0.0,
    upper: float = 1.0
) -> TobitReg:
    """
    Fits a Tobit regression model for interval-censored data.

    This function wraps statsmodels' TobitReg to handle effect size data
    that may be censored (e.g., when exact values are not reported).

    The Tobit model is appropriate for:
    - Left-censored data (values below a threshold)
    - Right-censored data (values above a threshold)
    - Interval-censored data (values within a range)

    Args:
        X: Feature matrix of shape (n, p) where n is the number of observations
           and p is the number of features. Should include a column of 1s if
           an intercept is desired.
        y: Target vector of shape (n,) containing the observed values or bounds.
           For interval-censored data, this should contain the observed values
           or the midpoint of intervals.
        lower: Lower bound for censoring (default: 0.0). Values below this are
               considered left-censored.
        upper: Upper bound for censoring (default: 1.0). Values above this are
               considered right-censored.

    Returns:
        Fitted TobitReg model instance from statsmodels.

    Raises:
        ValueError: If input dimensions don't match or if X is empty.
        TypeError: If inputs are not numpy arrays.
    """
    # Input validation
    if not isinstance(X, np.ndarray) or not isinstance(y, np.ndarray):
        raise TypeError("X and y must be numpy arrays")

    if X.shape[0] != y.shape[0]:
        raise ValueError(
            f"X and y must have the same number of observations. "
            f"Got X.shape={X.shape}, y.shape={y.shape}"
        )

    if X.shape[0] == 0:
        raise ValueError("X and y cannot be empty")

    # Ensure 2D array for X
    if X.ndim == 1:
        X = X.reshape(-1, 1)

    # Convert y to float array
    y = y.astype(float)

    # Check for NaN or Inf values
    if np.any(np.isnan(X)) or np.any(np.isnan(y)):
        raise ValueError("Input arrays contain NaN values")
    if np.any(np.isinf(X)) or np.any(np.isinf(y)):
        raise ValueError("Input arrays contain Inf values")

    # Prepare censoring indicators for TobitReg
    # TobitReg expects:
    # - left: array of left censoring limits (or -inf for uncensored)
    # - right: array of right censoring limits (or +inf for uncensored)
    # - y: observed values (or midpoint for interval-censored)

    left = np.full_like(y, -np.inf, dtype=float)
    right = np.full_like(y, np.inf, dtype=float)

    # Apply censoring bounds
    # For values exactly at bounds, we treat them as censored
    # For values within bounds, we treat them as uncensored
    for i in range(len(y)):
        if y[i] <= lower:
            left[i] = lower
            right[i] = lower  # Left-censored at lower bound
        elif y[i] >= upper:
            left[i] = upper
            right[i] = upper  # Right-censored at upper bound
        else:
            # Uncensored or interval-censored within bounds
            left[i] = lower
            right[i] = upper

    # Fit the Tobit model
    # Note: statsmodels TobitReg uses a different interface than typical
    # We need to pass the data in the format it expects
    try:
        model = TobitReg(
            endog=y,
            exog=X,
            left=lower,
            right=upper
        )
        result = model.fit()
        return result
    except Exception as e:
        raise RuntimeError(f"Failed to fit Tobit model: {str(e)}")


def prepare_censored_data(
    p_values: np.ndarray,
    bounds: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepares p-value data for Tobit analysis by converting inequalities to bounds.

    Args:
        p_values: Array of p-values (exact or inequality strings).
        bounds: Array of tuples (lower, upper) for each p-value.

    Returns:
        Tuple of (X_design, y_values, censoring_flags):
            - X_design: Design matrix for regression (with intercept)
            - y_values: Midpoint values for analysis
            - censoring_flags: Boolean array indicating censored observations
    """
    n = len(p_values)
    if n != len(bounds):
        raise ValueError("p_values and bounds must have the same length")

    y_values = np.zeros(n)
    censoring_flags = np.zeros(n, dtype=bool)

    for i in range(n):
        lower, upper, p_type = bounds[i]
        if p_type == "inequality":
            # Use midpoint for interval-censored data
            y_values[i] = (lower + upper) / 2.0
            censoring_flags[i] = True
        else:
            y_values[i] = lower  # For exact values, lower == upper
            censoring_flags[i] = False

    # Create design matrix with intercept
    X_design = np.column_stack([np.ones(n), np.arange(n)])  # Placeholder; actual features should be provided

    return X_design, y_values, censoring_flags