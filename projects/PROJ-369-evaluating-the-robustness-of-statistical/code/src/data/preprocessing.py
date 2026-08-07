import logging
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import linregress
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

def handle_missing_values(series: pd.Series, method: str = 'linear') -> pd.Series:
    """
    Handle missing values in a time series using linear interpolation.
    
    Args:
        series: Input pandas Series
        method: Interpolation method (default: 'linear')
        
    Returns:
        Series with missing values filled
        
    Raises:
        ValueError: If interpolation fails or gaps are too large for the method
    """
    if series.isna().sum() == 0:
        logger.debug("No missing values in series, returning as-is")
        return series
    
    logger.info(f"Found {series.isna().sum()} missing values in series. Interpolating...")
    
    try:
        interpolated = series.interpolate(method=method, limit_direction='both')
        
        # Check if any missing values remain
        if interpolated.isna().sum() > 0:
            logger.warning(f"Interpolation failed to fill all missing values. "
                         f"Remaining: {interpolated.isna().sum()}")
            # For the last/first NaNs that interpolation can't fill, use forward/backward fill
            interpolated = interpolated.fillna(method='ffill').fillna(method='bfill')
            
        if interpolated.isna().sum() > 0:
            raise ValueError(f"Could not fill all missing values. {interpolated.isna().sum()} remain.")
            
        return interpolated
    except Exception as e:
        logger.error(f"Error during interpolation: {e}")
        raise

def check_stationarity_adf(series: pd.Series, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform Augmented Dickey-Fuller test for stationarity.
    
    Args:
        series: Input pandas Series
        alpha: Significance level (default: 0.05)
        
    Returns:
        Dictionary with test results
    """
    try:
        result = stats.adfuller(series.dropna(), autolag='AIC')
        return {
            'statistic': result[0],
            'pvalue': result[1],
            'critical_values': result[4],
            'is_stationary': result[1] < alpha,
            'pvalue_threshold': alpha
        }
    except Exception as e:
        logger.error(f"ADF test failed: {e}")
        raise

def make_stationary(series: pd.Series, method: str = 'auto', 
                   max_diff_order: int = 3) -> Tuple[pd.Series, Dict[str, Any]]:
    """
    Make a time series stationary via differencing or detrending.
    
    Args:
        series: Input pandas Series
        method: 'auto', 'diff', or 'detrend'
        max_diff_order: Maximum differencing order to try
        
    Returns:
        Tuple of (stationary_series, transformation_info)
    """
    transformation_info = {
        'original_length': len(series),
        'transformations_applied': [],
        'final_stationary': False,
        'method': method
    }
    
    current_series = series.copy()
    
    if method == 'auto':
        # Try differencing first
        for order in range(1, max_diff_order + 1):
            adf_result = check_stationarity_adf(current_series)
            if adf_result['is_stationary']:
                transformation_info['final_stationary'] = True
                transformation_info['stationarity_method'] = f'ADF (p={adf_result["pvalue"]:.4f})'
                break
            
            # Apply differencing
            current_series = current_series.diff().dropna()
            transformation_info['transformations_applied'].append(f'diff_{order}')
            
            if len(current_series) < 25:
                logger.warning(f"Series too short after {order} differences ({len(current_series)} points). "
                             f"Stopping differencing.")
                break
        
        if not transformation_info['final_stationary']:
            # Try detrending
            logger.info("Differencing did not achieve stationarity. Trying detrending...")
            current_series, detrend_info = _detrend_series(current_series)
            transformation_info['transformations_applied'].extend(detrend_info['applied'])
            transformation_info['method'] = 'detrend'
    elif method == 'diff':
        for order in range(1, max_diff_order + 1):
            adf_result = check_stationarity_adf(current_series)
            if adf_result['is_stationary']:
                transformation_info['final_stationary'] = True
                transformation_info['stationarity_method'] = f'ADF (p={adf_result["pvalue"]:.4f})'
                break
            
            current_series = current_series.diff().dropna()
            transformation_info['transformations_applied'].append(f'diff_{order}')
            
            if len(current_series) < 25:
                break
    elif method == 'detrend':
        current_series, detrend_info = _detrend_series(current_series)
        transformation_info['transformations_applied'].extend(detrend_info['applied'])
        transformation_info['method'] = 'detrend'
    
    return current_series, transformation_info

def _detrend_series(series: pd.Series) -> Tuple[pd.Series, Dict[str, Any]]:
    """
    Detrend a series by removing linear trend.
    
    Args:
        series: Input pandas Series
        
    Returns:
        Tuple of (detrended_series, info)
    """
    info = {'applied': [], 'trend_removed': False}
    
    if len(series) < 2:
        logger.warning("Series too short for detrending")
        return series, info
    
    try:
        x = np.arange(len(series))
        y = series.dropna().values
        
        if len(y) < 2:
            return series, info
        
        slope, intercept, r_value, p_value, std_err = linregress(x[:len(y)], y)
        
        trend = slope * x + intercept
        detrended = series - trend
        
        info['applied'].append('linear_detrend')
        info['trend_removed'] = True
        info['slope'] = slope
        info['r_squared'] = r_value ** 2
        
        return detrended, info
    except Exception as e:
        logger.error(f"Detrending failed: {e}")
        return series, info

def resample_uk_load_data(series: pd.Series, target_freq: str = 'H') -> pd.Series:
    """
    Resample UK National Grid Load data to a consistent frequency.
    
    Args:
        series: Input pandas Series with datetime index
        target_freq: Target frequency (default: 'H' for hourly)
        
    Returns:
        Resampled series
    """
    if not isinstance(series.index, pd.DatetimeIndex):
        raise ValueError("Series must have a DatetimeIndex for resampling")
    
    logger.info(f"Resampling UK load data to {target_freq} frequency")
    
    try:
        resampled = series.resample(target_freq).mean()
        # Handle any new missing values from resampling
        resampled = handle_missing_values(resampled)
        return resampled
    except Exception as e:
        logger.error(f"Resampling failed: {e}")
        raise

def process_series_for_stationarity(series: pd.Series, series_name: str = "unknown") -> pd.Series:
    """
    Process a series for stationarity with edge case handling.
    
    Args:
        series: Input pandas Series
        series_name: Name of the series for logging
        
    Returns:
        Processed series (stationary or original if too short)
    """
    # Edge case: Skip datasets with < 25 points
    if len(series) < 25:
        logger.warning(f"Skipping stationarity processing for '{series_name}': "
                     f"Only {len(series)} points (minimum 25 required). "
                     f"Series will be used as-is with a warning.")
        return series
    
    try:
        stationary_series, info = make_stationary(series, method='auto')
        
        if info['final_stationary']:
            logger.info(f"Series '{series_name}' made stationary via: "
                      f"{', '.join(info['transformations_applied'])}")
        else:
            logger.warning(f"Could not achieve stationarity for '{series_name}' after "
                         f"{len(info['transformations_applied'])} transformations. "
                         f"Using best effort result.")
        
        return stationary_series
    except Exception as e:
        logger.error(f"Stationarity processing failed for '{series_name}': {e}")
        raise

def preprocess_dataset(dataset: pd.DataFrame, datetime_col: str = None, 
                      value_col: str = None) -> Dict[str, Any]:
    """
    Full preprocessing pipeline for a dataset.
    
    Args:
        dataset: Input DataFrame
        datetime_col: Name of datetime column (if not already index)
        value_col: Name of value column to process
        
    Returns:
        Dictionary with processed data and metadata
    """
    result = {
        'processed_data': None,
        'metadata': {},
        'warnings': []
    }
    
    # Set datetime index if needed
    if datetime_col and datetime_col in dataset.columns:
        dataset = dataset.set_index(datetime_col)
        if not isinstance(dataset.index, pd.DatetimeIndex):
            dataset.index = pd.to_datetime(dataset.index)
    
    # Determine value column
    if value_col:
        series = dataset[value_col]
    elif len(dataset.columns) == 1:
        series = dataset.iloc[:, 0]
    else:
        # Process first numeric column
        numeric_cols = dataset.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            series = dataset[numeric_cols[0]]
            result['warnings'].append(f"Processed first numeric column: {numeric_cols[0]}")
        else:
            raise ValueError("No numeric columns found in dataset")
    
    # Handle missing values
    series = handle_missing_values(series)
    
    # Check length before stationarity processing
    if len(series) < 25:
        result['warnings'].append(f"Series has only {len(series)} points. "
                                 f"Skipping stationarity processing.")
        result['processed_data'] = series
        result['metadata']['stationarity_processed'] = False
        result['metadata']['original_length'] = len(dataset)
        result['metadata']['processed_length'] = len(series)
        return result
    
    # Process for stationarity
    stationary_series, info = make_stationary(series, method='auto')
    
    result['processed_data'] = stationary_series
    result['metadata']['stationarity_processed'] = True
    result['metadata']['transformations'] = info['transformations_applied']
    result['metadata']['final_stationary'] = info['final_stationary']
    result['metadata']['original_length'] = len(dataset)
    result['metadata']['processed_length'] = len(stationary_series)
    
    return result