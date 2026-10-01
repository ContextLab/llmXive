"""
Stratification module for time series analysis.

This module provides functions to perform STL decomposition on time series
data and derive trend strength metrics for stratification purposes.
"""
from __future__ import annotations

import logging
from typing import Tuple, Optional

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL

logger = logging.getLogger(__name__)


def stl_decompose_train_only(
    series: pd.Series,
    seasonal_period: int,
    seasonal: float = 2.0,
    trend: Optional[float] = None,
    low_pass: Optional[float] = None
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Perform STL decomposition on the training split of a time series.

    This function explicitly enforces that decomposition uses only the
    provided training data to prevent data leakage. It does not look
    ahead to test data.

    Args:
        series: The input time series (typically the training split).
        seasonal_period: The period of seasonality (e.g., 12 for monthly data).
        seasonal: Smoothing parameter for seasonal component.
        trend: Smoothing parameter for trend component.
        low_pass: Smoothing parameter for low-pass filter.

    Returns:
        A tuple containing:
            - trend (pd.Series): The trend component.
            - seasonal (pd.Series): The seasonal component.
            - residual (pd.Series): The residual component.

    Raises:
        ValueError: If the series is too short for the specified period.
        RuntimeError: If STL decomposition fails to converge.
    """
    # Enforce minimum length for STL decomposition
    # STL requires at least 2 periods to estimate seasonality and trend
    if len(series) < 2 * seasonal_period:
        raise ValueError(
            f"Series length ({len(series)}) is too short for "
            f"seasonal period {seasonal_period}. Minimum required: {2 * seasonal_period}"
        )

    try:
        stl = STL(
            series,
            seasonal=seasonal,
            trend=trend,
            low_pass=low_pass,
            seasonal_deg=1,
            trend_deg=1,
            low_pass_deg=1,
            robust=True,
            seasonal_jump=1,
            trend_jump=1,
            low_pass_jump=1
        )
        result = stl.fit()

        return result.trend, result.seasonal, result.resid

    except Exception as e:
        logger.error(f"STL decomposition failed for series of length {len(series)}: {e}")
        raise RuntimeError(f"STL decomposition failed: {e}") from e


def calculate_trend_strength(
    series: pd.Series,
    seasonal_period: int,
    min_series_length: int = 10
) -> float:
    """
    Calculate the trend strength of a time series using STL decomposition.

    Trend strength is defined as the variance ratio:
    1 - Var(residuals) / Var(series - seasonal)

    A series is considered to have "high" trend strength if this ratio is > 0.5.

    This function operates ONLY on the provided series, ensuring no leakage
    from future data points. It handles short series gracefully by returning
    a default value instead of crashing.

    Args:
        series: The input time series.
        seasonal_period: The period of seasonality.
        min_series_length: Minimum length of series required for calculation.

    Returns:
        float: The trend strength value between 0 and 1.
               Returns 0.0 (indicating 'low' trend) if series is too short
               or calculation fails.
    """
    # Check if series is too short for STL decomposition
    # STL requires at least 2 periods to function
    if len(series) < 2 * seasonal_period:
        logger.warning(
            f"Series length ({len(series)}) is too short for STL decomposition "
            f"(requires at least {2 * seasonal_period} for seasonal period {seasonal_period}). "
            f"Assigning default 'low' trend strength (0.0)."
        )
        return 0.0

    if len(series) < min_series_length:
        logger.warning(
            f"Series length ({len(series)}) is below absolute minimum ({min_series_length}). "
            f"Returning 0.0 trend strength."
        )
        return 0.0

    try:
        trend, seasonal, residual = stl_decompose_train_only(
            series, seasonal_period
        )

        # Calculate variance of residuals
        var_residuals = np.var(residual)

        # Calculate variance of deseasonalized series (series - seasonal)
        deseasonalized = series - seasonal
        var_deseasonalized = np.var(deseasonalized)

        if var_deseasonalized == 0:
            logger.warning("Variance of deseasonalized series is zero. Returning 0.0 trend strength.")
            return 0.0

        trend_strength = 1 - (var_residuals / var_deseasonalized)

        # Clamp to [0, 1] range to handle numerical errors
        return float(np.clip(trend_strength, 0.0, 1.0))

    except ValueError as e:
        # This catches the "too short" error from stl_decompose_train_only
        # and logs it as a warning, returning 0.0
        logger.warning(
            f"Series too short for trend strength calculation: {e}. "
            f"Assigning default 'low' trend strength (0.0)."
        )
        return 0.0
    except Exception as e:
        logger.warning(f"Failed to calculate trend strength: {e}. Returning 0.0.")
        return 0.0


def classify_trend_strength(
    series: pd.Series,
    seasonal_period: int,
    threshold: float = 0.5
) -> str:
    """
    Classify a time series as having 'high' or 'low' trend strength.

    This function handles short series gracefully by returning 'low'
    for series that are too short for STL decomposition.

    Args:
        series: The input time series.
        seasonal_period: The period of seasonality.
        threshold: The threshold value for classification (default 0.5).

    Returns:
        str: 'high' if trend strength > threshold, 'low' otherwise.
             Returns 'low' for series that are too short.
    """
    strength = calculate_trend_strength(series, seasonal_period)
    return "high" if strength > threshold else "low"


def extract_seasonality_flags(
    series: pd.Series,
    seasonal_period: int,
    threshold: float = 0.1
) -> str:
    """
    Determine if a time series exhibits significant seasonality.

    This uses the ratio of seasonal variance to total variance.
    Handles short series gracefully by returning 'no' for series
    that are too short for STL decomposition.

    Args:
        series: The input time series.
        seasonal_period: The period of seasonality.
        threshold: Minimum ratio to consider seasonality significant.

    Returns:
        str: 'yes' if seasonality is significant, 'no' otherwise.
             Returns 'no' for series that are too short.
    """
    # STL requires at least 2 periods
    if len(series) < 2 * seasonal_period:
        logger.warning(
            f"Series length ({len(series)}) is too short for seasonality detection "
            f"(requires at least {2 * seasonal_period}). Returning 'no'."
        )
        return "no"

    try:
        _, seasonal, _ = stl_decompose_train_only(series, seasonal_period)

        var_seasonal = np.var(seasonal)
        var_total = np.var(series)

        if var_total == 0:
            return "no"

        ratio = var_seasonal / var_total
        return "yes" if ratio > threshold else "no"

    except ValueError as e:
        # Catch series too short errors
        logger.warning(
            f"Series too short for seasonality detection: {e}. Returning 'no'."
        )
        return "no"
    except Exception as e:
        logger.warning(f"Failed to extract seasonality flags: {e}. Returning 'no'.")
        return "no"