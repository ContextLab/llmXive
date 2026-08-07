"""
Preprocessing module for time series data.
Implements missing value interpolation, stationarity checks (ADF),
detrending (linear regression), and differencing.
"""
import logging
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller
from statsmodels.regression.linear_model import OLS
from typing import Tuple, List, Dict, Any, Optional, Union

from src.utils.logging import get_logger
from src.data.schemas import TimeSeries

logger = get_logger(__name__)


class PreprocessingError(Exception):
    """Custom exception for preprocessing errors."""
    pass


def interpolate_missing(series: pd.Series, method: str = 'linear') -> pd.Series:
    """
    Interpolate missing values in a time series.

    Args:
        series: Input pandas Series with potential NaN values.
        method: Interpolation method ('linear', 'time', 'pad', etc.).

    Returns:
        Series with missing values filled.

    Raises:
        PreprocessingError: If interpolation fails or leaves NaNs at boundaries.
    """
    if not isinstance(series, pd.Series):
        raise PreprocessingError(f"Expected pandas Series, got {type(series)}")

    if series.isna().sum() == 0:
        return series.copy()

    logger.debug(f"Interpolating {series.isna().sum()} missing values using {method}")

    try:
        interpolated = series.interpolate(method=method, limit_direction='both')
    except Exception as e:
        raise PreprocessingError(f"Interpolation failed: {str(e)}")

    # Check if any NaNs remain (e.g., at boundaries if limit_direction wasn't 'both')
    if interpolated.isna().any():
        # Try forward/backward fill for remaining boundary NaNs
        interpolated = interpolated.ffill().bfill()
        if interpolated.isna().any():
            raise PreprocessingError(
                f"Interpolation left {interpolated.isna().sum()} missing values at boundaries. "
                "Series length may be insufficient or all values are missing."
            )

    return interpolated


def check_stationarity_adf(series: pd.Series, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Check stationarity using the Augmented Dickey-Fuller (ADF) test.

    Args:
        series: Input time series.
        alpha: Significance level for the test.

    Returns:
        Dictionary containing:
            - 'stationary': bool (True if p-value < alpha)
            - 'p_value': float
            - 'statistic': float
            - 'critical_values': dict

    Raises:
        PreprocessingError: If the series is too short or ADF fails.
    """
    if not isinstance(series, (pd.Series, np.ndarray)):
        raise PreprocessingError(f"Expected Series or array, got {type(series)}")

    clean_series = pd.Series(series).dropna()
    if len(clean_series) < 10:
        raise PreprocessingError(
            f"Series too short for ADF test (length={len(clean_series)}, min=10)"
        )

    try:
        result = adfuller(clean_series, autolag='AIC')
    except Exception as e:
        raise PreprocessingError(f"ADF test failed: {str(e)}")

    p_value = result[1]
    stationary = p_value < alpha

    logger.debug(
        f"ADF Test: p-value={p_value:.4f}, "
        f"{'Stationary' if stationary else 'Non-stationary'} at alpha={alpha}"
    )

    return {
        'stationary': stationary,
        'p_value': p_value,
        'statistic': result[0],
        'critical_values': result[4],
        'n_lags': result[2]
    }


def detrend_linear(series: pd.Series) -> Tuple[pd.Series, Dict[str, float]]:
    """
    Detrend a series using linear regression residuals.

    Args:
        series: Input time series.

    Returns:
        Tuple of (detrended_series, regression_stats) where regression_stats contains:
            - 'slope': float
            - 'intercept': float
            - 'r_squared': float

    Raises:
        PreprocessingError: If regression fails.
    """
    if not isinstance(series, pd.Series):
        raise PreprocessingError(f"Expected pandas Series, got {type(series)}")

    clean_series = series.dropna()
    n = len(clean_series)
    if n < 3:
        raise PreprocessingError(
            f"Series too short for linear detrending (length={n}, min=3)"
        )

    # Create time index
    t = np.arange(n)

    try:
        # Fit linear regression: y = slope * t + intercept
        model = OLS(clean_series.values, np.column_stack([np.ones(n), t])).fit()
        residuals = model.resid
        slope = model.params[1]
        intercept = model.params[0]
        r_squared = model.rsquared

        logger.debug(
            f"Linear detrending: slope={slope:.6f}, "
            f"intercept={intercept:.6f}, R²={r_squared:.4f}"
        )

        # Create detrended series with original index
        detrended = pd.Series(residuals, index=clean_series.index)

        return detrended, {
            'slope': float(slope),
            'intercept': float(intercept),
            'r_squared': float(r_squared)
        }

    except Exception as e:
        raise PreprocessingError(f"Linear detrending failed: {str(e)}")


def difference(series: pd.Series, order: int = 1) -> pd.Series:
    """
    Apply differencing to a series to achieve stationarity.

    Args:
        series: Input time series.
        order: Order of differencing (1 for first difference, 2 for second, etc.).

    Returns:
        Differenced series.

    Raises:
        PreprocessingError: If differencing fails or results in empty series.
    """
    if not isinstance(series, pd.Series):
        raise PreprocessingError(f"Expected pandas Series, got {type(series)}")

    clean_series = series.dropna()
    if len(clean_series) <= order:
        raise PreprocessingError(
            f"Series too short for differencing of order {order} "
            f"(length={len(clean_series)})"
        )

    try:
        differenced = clean_series.diff(periods=1)
        for _ in range(order - 1):
            differenced = differenced.diff(periods=1)

        differenced = differenced.dropna()

        if len(differenced) == 0:
            raise PreprocessingError("Differencing resulted in empty series")

        logger.debug(f"Differenced series of order {order}, new length: {len(differenced)}")

        return differenced

    except Exception as e:
        raise PreprocessingError(f"Differencing failed: {str(e)}")


def preprocess_series(
    series: pd.Series,
    require_stationarity: bool = True,
    max_differences: int = 3,
    alpha: float = 0.05
) -> Tuple[pd.Series, Dict[str, Any]]:
    """
    Full preprocessing pipeline for a single series:
    1. Interpolate missing values
    2. Check stationarity (ADF)
    3. If non-stationary: try differencing up to max_differences
       OR detrend if differencing fails to achieve stationarity

    Args:
        series: Input time series.
        require_stationarity: If True, enforce stationarity before returning.
        max_differences: Maximum number of differencing operations.
        alpha: Significance level for ADF test.

    Returns:
        Tuple of (preprocessed_series, processing_log) where processing_log contains:
            - 'n_missing_interpolated': int
            - 'initial_stationary': bool
            - 'n_differences': int (0 if not differenced)
            - 'was_detrended': bool
            - 'final_stationary': bool
            - 'final_p_value': float
            - 'steps': list of strings describing operations

    Raises:
        PreprocessingError: If preprocessing fails or cannot achieve stationarity.
    """
    if not isinstance(series, pd.Series):
        raise PreprocessingError(f"Expected pandas Series, got {type(series)}")

    if len(series) < 25:
        logger.warning(f"Series length {len(series)} is below recommended minimum (25)")

    log = {
        'n_missing_interpolated': 0,
        'initial_stationary': False,
        'n_differences': 0,
        'was_detrended': False,
        'final_stationary': False,
        'final_p_value': None,
        'steps': []
    }

    current = series.copy()

    # Step 1: Interpolate missing values
    missing_count = current.isna().sum()
    if missing_count > 0:
        current = interpolate_missing(current)
        log['n_missing_interpolated'] = missing_count
        log['steps'].append(f"Interpolated {missing_count} missing values")

    if len(current) == 0:
        raise PreprocessingError("Series became empty after interpolation")

    # Step 2: Check initial stationarity
    adf_result = check_stationarity_adf(current, alpha=alpha)
    log['initial_stationary'] = adf_result['stationary']
    log['steps'].append(
        f"Initial ADF: p={adf_result['p_value']:.4f}, "
        f"{'stationary' if adf_result['stationary'] else 'non-stationary'}"
    )

    if not require_stationarity:
        return current, log

    if adf_result['stationary']:
        log['final_stationary'] = True
        log['final_p_value'] = adf_result['p_value']
        return current, log

    # Step 3: Try differencing
    for i in range(1, max_differences + 1):
        try:
            current = difference(current, order=i)
            log['n_differences'] = i
            log['steps'].append(f"Applied difference of order {i}")

            adf_result = check_stationarity_adf(current, alpha=alpha)
            log['steps'].append(
                f"After diff {i}: ADF p={adf_result['p_value']:.4f}, "
                f"{'stationary' if adf_result['stationary'] else 'non-stationary'}"
            )

            if adf_result['stationary']:
                log['final_stationary'] = True
                log['final_p_value'] = adf_result['p_value']
                return current, log

        except PreprocessingError as e:
            logger.warning(f"Differencing order {i} failed: {str(e)}")
            continue

    # Step 4: If differencing failed, try detrending
    logger.info("Differencing did not achieve stationarity. Attempting linear detrending.")
    try:
        current, detrend_stats = detrend_linear(current)
        log['was_detrended'] = True
        log['steps'].append(
            f"Detrended (slope={detrend_stats['slope']:.4f}, "
            f"R²={detrend_stats['r_squared']:.4f})"
        )

        adf_result = check_stationarity_adf(current, alpha=alpha)
        log['steps'].append(
            f"After detrend: ADF p={adf_result['p_value']:.4f}, "
            f"{'stationary' if adf_result['stationary'] else 'non-stationary'}"
        )

        if adf_result['stationary']:
            log['final_stationary'] = True
            log['final_p_value'] = adf_result['p_value']
            return current, log

        raise PreprocessingError(
            f"Could not achieve stationarity after differencing and detrending. "
            f"Final p-value: {adf_result['p_value']:.4f}"
        )

    except PreprocessingError as e:
        raise PreprocessingError(f"Detrending failed: {str(e)}")


def preprocess_dataset(
    df: pd.DataFrame,
    value_column: str,
    time_column: Optional[str] = None,
    **kwargs
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Preprocess a dataset (DataFrame) containing a time series column.

    Args:
        df: Input DataFrame.
        value_column: Name of the column containing the time series values.
        time_column: Name of the time index column (optional, uses range if not provided).
        **kwargs: Arguments passed to preprocess_series.

    Returns:
        Tuple of (preprocessed_df, metadata) where:
            - preprocessed_df: DataFrame with 'original' and 'processed' columns
            - metadata: Dict with processing details per column (if multiple)

    Raises:
        PreprocessingError: If preprocessing fails for the dataset.
    """
    if not isinstance(df, pd.DataFrame):
        raise PreprocessingError(f"Expected DataFrame, got {type(df)}")

    if value_column not in df.columns:
        raise PreprocessingError(f"Column '{value_column}' not found in DataFrame")

    # Set time index if provided
    if time_column and time_column in df.columns:
        df = df.set_index(time_column)

    # Extract series
    series = df[value_column]
    processed_series, log = preprocess_series(series, **kwargs)

    # Create output DataFrame
    result_df = pd.DataFrame({
        'original': series,
        'processed': processed_series
    })

    # Align indices (processed might be shorter due to differencing)
    result_df = result_df.loc[processed_series.index]

    metadata = {
        'column': value_column,
        'original_length': len(series),
        'processed_length': len(processed_series),
        'preprocessing_log': log
    }

    logger.info(
        f"Preprocessed '{value_column}': "
        f"{log['n_missing_interpolated']} interpolated, "
        f"{log['n_differences']} differences, "
        f"detrended={log['was_detrended']}, "
        f"stationary={log['final_stationary']}"
    )

    return result_df, metadata


# Aliases for backward compatibility / convenience
interpolate_missing_values = interpolate_missing
check_stationarity = check_stationarity_adf
detrend_series = detrend_linear
difference_series = difference
preprocess = preprocess_series