import logging
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller
from statsmodels.regression.linear_model import OLS

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
        Series with missing values interpolated.
    """
    if series.isna().all():
        raise PreprocessingError("Cannot interpolate: series is entirely NaN.")

    # Use pandas built-in interpolation
    interpolated = series.interpolate(method=method, limit_direction='both')

    # Check if any NaNs remain (e.g., at the edges if method doesn't cover them)
    if interpolated.isna().any():
        # Forward fill then backward fill for any remaining edge cases
        interpolated = interpolated.ffill().bfill()

    if interpolated.isna().any():
        raise PreprocessingError("Interpolation failed: NaN values remain after interpolation.")

    return interpolated

def check_stationarity_adf(series: pd.Series, alpha: float = 0.05) -> dict:
    """
    Perform Augmented Dickey-Fuller test for stationarity.

    Args:
        series: Input pandas Series.
        alpha: Significance level for the test.

    Returns:
        Dictionary containing 'is_stationary' (bool) and 'p_value' (float).
    """
    if len(series) < 10:
        raise PreprocessingError("Series too short for ADF test (min 10 points).")

    try:
        result = adfuller(series.dropna(), autolag='AIC')
        p_value = result[1]
        is_stationary = p_value < alpha
        return {
            'is_stationary': is_stationary,
            'p_value': p_value,
            'statistic': result[0],
            'critical_values': result[4]
        }
    except Exception as e:
        raise PreprocessingError(f"ADF test failed: {str(e)}")

def detrend_linear(series: pd.Series) -> pd.Series:
    """
    Detrend a time series using linear regression residuals.

    Args:
        series: Input pandas Series.

    Returns:
        Residuals from linear regression (detrended series).
    """
    if len(series) < 2:
        raise PreprocessingError("Series too short for linear detrending.")

    # Create time index
    n = len(series)
    x = np.arange(n).reshape(-1, 1)
    y = series.values

    # Fit linear regression
    model = OLS(y, x).fit()
    residuals = model.resid

    # Return as Series with original index
    return pd.Series(residuals, index=series.index)

def difference_series(series: pd.Series, order: int = 1) -> pd.Series:
    """
    Apply differencing to a time series.

    Args:
        series: Input pandas Series.
        order: Order of differencing.

    Returns:
        Differenced series.
    """
    if order < 1:
        return series

    result = series.diff().dropna()
    for _ in range(order - 1):
        result = result.diff().dropna()

    return result

def resample_to_consistent_frequency(series: pd.Series, target_freq: str = None) -> pd.Series:
    """
    Resample a time series to a consistent frequency based on native resolution.

    This implements US1-AC3: resample datasets to a consistent frequency (e.g., hourly, daily)
    based on the dataset's native resolution before stationarity testing.

    Args:
        series: Input pandas Series with DatetimeIndex.
        target_freq: Target frequency string (e.g., 'H', 'D', 'MS'). If None, auto-detect.

    Returns:
        Resampled Series.

    Raises:
        PreprocessingError: If resampling fails or frequency detection is ambiguous.
    """
    if not isinstance(series.index, pd.DatetimeIndex):
        raise PreprocessingError("Series index must be a DatetimeIndex for resampling.")

    if series.isna().any():
        raise PreprocessingError("Cannot resample series with missing values. Interpolate first.")

    # Auto-detect native frequency if not provided
    if target_freq is None:
        # Calculate time differences
        diffs = series.index.to_series().diff().dropna()
        if len(diffs) == 0:
            raise PreprocessingError("Cannot determine frequency: insufficient data points.")

        # Get median time difference
        median_diff = diffs.median()
        median_diff_hours = median_diff.total_seconds() / 3600

        # Determine appropriate target frequency based on native resolution
        if median_diff_hours < 1:
            # Sub-hourly data: resample to hourly
            target_freq = 'H'
        elif median_diff_hours < 24:
            # Sub-daily but >= hourly: resample to hourly
            target_freq = 'H'
        elif median_diff_hours < 7 * 24:
            # Sub-weekly but >= daily: resample to daily
            target_freq = 'D'
        elif median_diff_hours < 30 * 24:
            # Sub-monthly but >= weekly: resample to weekly
            target_freq = 'W'
        else:
            # Monthly or coarser: resample to monthly
            target_freq = 'MS'

        logging.info(f"Auto-detected native frequency ~{median_diff_hours:.1f}h, resampling to {target_freq}")

    # Perform resampling
    # For most cases, we'll use mean aggregation, but handle different data types appropriately
    try:
        resampled = series.resample(target_freq).mean()
    except Exception as e:
        raise PreprocessingError(f"Resampling to {target_freq} failed: {str(e)}")

    # Check for NaNs introduced by resampling (gaps in data)
    if resampled.isna().any():
        logging.warning(f"Resampling introduced {resampled.isna().sum()} NaN values. Interpolating...")
        resampled = resampled.interpolate(method='linear', limit_direction='both')
        resampled = resampled.ffill().bfill()

    if resampled.isna().any():
        raise PreprocessingError(f"Resampling to {target_freq} failed: NaN values remain after interpolation.")

    return resampled

def preprocess_series(series: pd.Series, require_stationarity: bool = True) -> pd.Series:
    """
    Preprocess a single time series: interpolate, resample, and ensure stationarity.

    Args:
        series: Input pandas Series.
        require_stationarity: If True, apply differencing/detrending until stationary.

    Returns:
        Preprocessed and stationary series.
    """
    logging.info(f"Starting preprocessing for series with {len(series)} points")

    # Step 1: Interpolate missing values
    series = interpolate_missing(series)

    # Step 2: Resample to consistent frequency (US1-AC3)
    series = resample_to_consistent_frequency(series)

    logging.info(f"After resampling: {len(series)} points")

    # Step 3: Check stationarity and transform if needed
    if require_stationarity:
        max_diffs = 5
        current_series = series
        diff_count = 0

        while diff_count < max_diffs:
            adf_result = check_stationarity_adf(current_series)
            if adf_result['is_stationary']:
                logging.info(f"Series is stationary after {diff_count} transformations (p={adf_result['p_value']:.4f})")
                return current_series

            # Not stationary: try detrending first (if not already differenced)
            if diff_count == 0:
                try:
                    detrended = detrend_linear(current_series)
                    # Check if detrending helped
                    adf_detrend = check_stationarity_adf(detrended)
                    if adf_detrend['is_stationary']:
                        logging.info("Series became stationary after linear detrending")
                        return detrended
                    # If detrending didn't work, fall back to differencing
                    logging.info("Detrending did not achieve stationarity, proceeding to differencing")
                except Exception as e:
                    logging.warning(f"Detrending failed: {e}, proceeding to differencing")

            # Apply differencing
            current_series = difference_series(current_series, order=1)
            diff_count += 1
            logging.info(f"Applied differencing #{diff_count}, new length: {len(current_series)}")

            if len(current_series) < 10:
                raise PreprocessingError("Series too short after differencing for stationarity testing.")

        raise PreprocessingError(f"Failed to achieve stationarity after {max_diffs} transformations.")

    return series

def preprocess_dataset(dataset: pd.DataFrame, value_column: str, date_column: str = None) -> pd.Series:
    """
    Preprocess an entire dataset: parse dates, select value column, and preprocess.

    Args:
        dataset: Input pandas DataFrame.
        value_column: Name of the column containing values.
        date_column: Name of the column containing dates. If None, assumes index is datetime.

    Returns:
        Preprocessed Series.
    """
    if date_column:
        if date_column not in dataset.columns:
            raise PreprocessingError(f"Date column '{date_column}' not found in dataset.")
        if value_column not in dataset.columns:
            raise PreprocessingError(f"Value column '{value_column}' not found in dataset.")

        dataset = dataset.copy()
        dataset[date_column] = pd.to_datetime(dataset[date_column])
        dataset.set_index(date_column, inplace=True)

    if not isinstance(dataset.index, pd.DatetimeIndex):
        raise PreprocessingError("Dataset must have a DatetimeIndex. Provide date_column or set index before calling.")

    series = dataset[value_column]

    if len(series) < 25:
        logging.warning(f"Series has only {len(series)} points (threshold: 25). Proceeding with caution.")

    return preprocess_series(series)

def interpolate_missing_values(series: pd.Series) -> pd.Series:
    """
    Wrapper for interpolate_missing to match expected API.

    Args:
        series: Input pandas Series.

    Returns:
        Series with missing values interpolated.
    """
    return interpolate_missing(series)
