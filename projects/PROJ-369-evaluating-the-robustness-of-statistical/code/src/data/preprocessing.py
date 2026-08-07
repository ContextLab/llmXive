"""
Preprocessing module for time series data.

Implements:
- Missing value interpolation (linear)
- Stationarity testing (ADF)
- Detrending (linear regression residuals)
- Differencing
"""
import logging
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller
from statsmodels.regression.linear_model import OLS
from typing import Union, Tuple, Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class PreprocessingError(Exception):
    """Custom exception for preprocessing errors."""
    pass

def interpolate_missing(series: Union[pd.Series, np.ndarray], method: str = 'linear') -> Union[pd.Series, np.ndarray]:
    """
    Interpolate missing values in a time series.
    
    Args:
        series: Input time series (pandas Series or numpy array)
        method: Interpolation method (default: 'linear')
    
    Returns:
        Interpolated series with no missing values
    
    Raises:
        PreprocessingError: If interpolation fails or all values are missing
    """
    if isinstance(series, np.ndarray):
        series = pd.Series(series)
    
    # Check if all values are missing
    if series.isna().all():
        raise PreprocessingError("Cannot interpolate: all values are missing")
    
    # Check if there are any missing values
    if not series.isna().any():
        logger.debug("No missing values to interpolate")
        return series
    
    try:
        # Use pandas interpolate with specified method
        interpolated = series.interpolate(method=method, limit_direction='both')
        
        # Check if interpolation was successful (no remaining NaN)
        if interpolated.isna().any():
            # Try forward fill then backward fill for any remaining NaN at edges
            interpolated = interpolated.ffill().bfill()
            
            if interpolated.isna().any():
                raise PreprocessingError(
                    f"Interpolation failed: {interpolated.isna().sum()} values remain missing "
                    f"after linear interpolation and fill"
                )
        
        logger.info(f"Successfully interpolated {series.isna().sum()} missing values using {method} method")
        return interpolated
        
    except Exception as e:
        raise PreprocessingError(f"Interpolation failed: {str(e)}")

def check_stationarity(series: Union[pd.Series, np.ndarray], alpha: float = 0.05) -> Tuple[bool, Dict[str, Any]]:
    """
    Check if a time series is stationary using the Augmented Dickey-Fuller test.
    
    Args:
        series: Input time series
        alpha: Significance level for the test (default: 0.05)
    
    Returns:
        Tuple of (is_stationary, test_results_dict)
    
    Raises:
        PreprocessingError: If the test fails or series is too short
    """
    if isinstance(series, np.ndarray):
        series = pd.Series(series)
    
    # Drop NaN values
    series = series.dropna()
    
    if len(series) < 10:
        raise PreprocessingError(
            f"Series too short for ADF test (n={len(series)}, need >= 10)"
        )
    
    try:
        result = adfuller(series, autolag='AIC')
        
        test_results = {
            'statistic': result[0],
            'pvalue': result[1],
            'usedlag': result[2],
            'nobs': result[3],
            'critical_values': result[4],
            'is_stationary': result[1] < alpha
        }
        
        logger.info(
            f"ADF test: statistic={result[0]:.4f}, p-value={result[1]:.4f}, "
            f"stationary={test_results['is_stationary']}"
        )
        
        return test_results['is_stationary'], test_results
        
    except Exception as e:
        raise PreprocessingError(f"ADF test failed: {str(e)}")

def detrend_series(series: Union[pd.Series, np.ndarray]) -> Tuple[Union[pd.Series, np.ndarray], Dict[str, Any]]:
    """
    Detrend a time series using linear regression residuals.
    
    Args:
        series: Input time series
    
    Returns:
        Tuple of (detrended_series, regression_stats)
    
    Raises:
        PreprocessingError: If detrending fails
    """
    if isinstance(series, np.ndarray):
        series = pd.Series(series)
    
    series = series.dropna()
    n = len(series)
    
    if n < 3:
        raise PreprocessingError(
            f"Series too short for detrending (n={n}, need >= 3)"
        )
    
    try:
        # Create time index
        t = np.arange(n)
        
        # Fit linear regression: series = beta0 + beta1*t + error
        model = OLS(series.values, np.column_stack([np.ones(n), t])).fit()
        
        # Get residuals (detrended series)
        residuals = model.resid
        
        regression_stats = {
            'slope': model.params[1],
            'intercept': model.params[0],
            'rsquared': model.rsquared,
            'pvalue_slope': model.pvalues[1],
            'f_pvalue': model.f_pvalue
        }
        
        logger.info(
            f"Detrending: slope={regression_stats['slope']:.6f}, "
            f"R²={regression_stats['rsquared']:.4f}, "
            f"p-value={regression_stats['pvalue_slope']:.4f}"
        )
        
        return pd.Series(residuals, index=series.index), regression_stats
        
    except Exception as e:
        raise PreprocessingError(f"Detrending failed: {str(e)}")

def difference_series(series: Union[pd.Series, np.ndarray], order: int = 1) -> Union[pd.Series, np.ndarray]:
    """
    Apply differencing to a time series.
    
    Args:
        series: Input time series
        order: Order of differencing (default: 1)
    
    Returns:
        Differenced series
    
    Raises:
        PreprocessingError: If differencing fails
    """
    if isinstance(series, np.ndarray):
        series = pd.Series(series)
    
    series = series.dropna()
    
    if order < 1:
        raise PreprocessingError("Order must be >= 1")
    
    try:
        for i in range(order):
            series = series.diff().dropna()
            
            if len(series) == 0:
                raise PreprocessingError(
                    f"Differencing order {order} resulted in empty series"
                )
        
        logger.info(f"Applied {order}th-order differencing, final length: {len(series)}")
        return series
        
    except Exception as e:
        raise PreprocessingError(f"Differencing failed: {str(e)}")

def preprocess_series(
    series: Union[pd.Series, np.ndarray],
    interpolate_missing_values: bool = True,
    max_differencing_order: int = 3,
    alpha: float = 0.05
) -> Tuple[Union[pd.Series, np.ndarray], Dict[str, Any]]:
    """
    Preprocess a time series: interpolate missing values, then ensure stationarity.
    
    Args:
        series: Input time series
        interpolate_missing_values: Whether to interpolate missing values (default: True)
        max_differencing_order: Maximum order of differencing to apply (default: 3)
        alpha: Significance level for ADF test (default: 0.05)
    
    Returns:
        Tuple of (preprocessed_series, preprocessing_log)
    
    Raises:
        PreprocessingError: If preprocessing fails
    """
    if isinstance(series, np.ndarray):
        series = pd.Series(series)
    
    preprocessing_log = {
        'original_length': len(series),
        'original_missing': int(series.isna().sum()),
        'interpolated': False,
        'stationary': False,
        'differencing_order': 0,
        'detrended': False,
        'final_length': 0,
        'steps': []
    }
    
    # Step 1: Interpolate missing values if requested
    if interpolate_missing_values:
        try:
            series = interpolate_missing(series)
            preprocessing_log['interpolated'] = True
            preprocessing_log['steps'].append('interpolated_missing_values')
        except PreprocessingError as e:
            logger.warning(f"Missing value interpolation skipped: {str(e)}")
            preprocessing_log['steps'].append(f'skipped_interpolation: {str(e)}')
    
    # Check if series is now too short
    series = series.dropna()
    if len(series) < 10:
        raise PreprocessingError(
            f"Series too short after preprocessing (n={len(series)}, need >= 10)"
        )
    
    # Step 2: Check stationarity
    is_stationary, adf_results = check_stationarity(series, alpha)
    preprocessing_log['stationary'] = is_stationary
    
    if is_stationary:
        preprocessing_log['steps'].append('already_stationary')
        preprocessing_log['final_length'] = len(series)
        return series, preprocessing_log
    
    # Step 3: Try detrending first
    try:
        detrended_series, detrend_stats = detrend_series(series)
        is_detrended_stationary, _ = check_stationarity(detrended_series, alpha)
        
        if is_detrended_stationary:
            series = detrended_series
            preprocessing_log['detrended'] = True
            preprocessing_log['steps'].append('detrended_and_stationary')
            preprocessing_log['final_length'] = len(series)
            return series, preprocessing_log
        
        logger.info("Detrending did not achieve stationarity, proceeding to differencing")
        preprocessing_log['steps'].append('detrend_not_stationary')
        
    except PreprocessingError as e:
        logger.warning(f"Detrending failed or not needed: {str(e)}")
        preprocessing_log['steps'].append(f'skipped_detrend: {str(e)}')
    
    # Step 4: Apply differencing until stationary or max order reached
    for order in range(1, max_differencing_order + 1):
        try:
            series = difference_series(series, order=order)
            is_stationary, _ = check_stationarity(series, alpha)
            
            if is_stationary:
                preprocessing_log['differencing_order'] = order
                preprocessing_log['steps'].append(f'differenced_order_{order}_stationary')
                preprocessing_log['final_length'] = len(series)
                return series, preprocessing_log
            
            logger.info(f"Order {order} differencing not sufficient, continuing...")
            preprocessing_log['steps'].append(f'differenced_order_{order}_not_stationary')
            
        except PreprocessingError as e:
            logger.warning(f"Differencing order {order} failed: {str(e)}")
            preprocessing_log['steps'].append(f'skipped_differencing_order_{order}: {str(e)}')
            break
    
    # If we reach here, we couldn't achieve stationarity
    raise PreprocessingError(
        f"Could not achieve stationarity after max differencing order ({max_differencing_order}). "
        f"Final series length: {len(series)}, ADF p-value: {adf_results['pvalue']:.4f}"
    )

def preprocess_dataset(
    df: pd.DataFrame,
    time_column: str,
    value_column: str,
    interpolate_missing_values: bool = True,
    max_differencing_order: int = 3,
    alpha: float = 0.05
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Preprocess a dataset containing time series data.
    
    Args:
        df: Input DataFrame
        time_column: Name of the time column
        value_column: Name of the value column
        interpolate_missing_values: Whether to interpolate missing values
        max_differencing_order: Maximum differencing order
        alpha: Significance level for ADF test
    
    Returns:
        Tuple of (preprocessed_df, dataset_preprocessing_log)
    
    Raises:
        PreprocessingError: If preprocessing fails
    """
    if time_column not in df.columns or value_column not in df.columns:
        raise PreprocessingError(
            f"Columns '{time_column}' and/or '{value_column}' not found in DataFrame"
        )
    
    # Set time as index
    df = df.copy()
    df[time_column] = pd.to_datetime(df[time_column])
    df = df.set_index(time_column)
    series = df[value_column]
    
    # Preprocess the series
    preprocessed_series, series_log = preprocess_series(
        series,
        interpolate_missing_values=interpolate_missing_values,
        max_differencing_order=max_differencing_order,
        alpha=alpha
    )
    
    # Create result DataFrame
    result_df = pd.DataFrame({value_column: preprocessed_series})
    
    dataset_log = {
        'dataset_columns': list(df.columns),
        'value_column': value_column,
        'series_log': series_log,
        'final_length': len(result_df)
    }
    
    logger.info(
        f"Dataset preprocessing complete: "
        f"original={series_log['original_length']}, "
        f"final={dataset_log['final_length']}, "
        f"stationary={series_log['stationary']}"
    )
    
    return result_df, dataset_log

# Backward compatibility aliases
def interpolate_missing_values(series, *args, **kwargs):
    """Alias for interpolate_missing for backward compatibility."""
    return interpolate_missing(series, *args, **kwargs)

def check_stationarity_adf(series, *args, **kwargs):
    """Alias for check_stationarity for backward compatibility."""
    return check_stationarity(series, *args, **kwargs)

def detrend_linear(series, *args, **kwargs):
    """Alias for detrend_series for backward compatibility."""
    return detrend_series(series, *args, **kwargs)

def difference(series, *args, **kwargs):
    """Alias for difference_series for backward compatibility."""
    return difference_series(series, *args, **kwargs)

def preprocess(
    series,
    interpolate_missing_values=True,
    max_differencing_order=3,
    alpha=0.05
):
    """Alias for preprocess_series for backward compatibility."""
    return preprocess_series(
        series,
        interpolate_missing_values=interpolate_missing_values,
        max_differencing_order=max_differencing_order,
        alpha=alpha
    )
