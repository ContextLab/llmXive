import logging
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller
from statsmodels.regression.linear_model import OLS
from typing import Tuple, Optional, Dict, Any, Union

class PreprocessingError(Exception):
    """Custom exception for preprocessing errors."""
    pass

def interpolate_missing(series: pd.Series) -> pd.Series:
    """
    Interpolate missing values using linear interpolation.
    
    Args:
        series: Input time series with potential NaN values
        
    Returns:
        Series with missing values interpolated
    """
    return series.interpolate(method='linear')

def check_stationarity_adf(series: pd.Series, alpha: float = 0.05) -> Tuple[bool, float]:
    """
    Check stationarity using the Augmented Dickey-Fuller test.
    
    Args:
        series: Input time series
        alpha: Significance level for the test
        
    Returns:
        Tuple of (is_stationary, p_value)
    """
    result = adfuller(series.dropna(), autolag='AIC')
    p_value = result[1]
    is_stationary = p_value < alpha
    return is_stationary, p_value

def detrend_linear(series: pd.Series) -> pd.Series:
    """
    Detrend a series using linear regression residuals.
    
    Args:
        series: Input time series
        
    Returns:
        Residuals from linear regression (detrended series)
    """
    n = len(series)
    if n < 2:
        raise PreprocessingError("Series too short for detrending")
        
    x = np.arange(n).reshape(-1, 1)
    y = series.values
    
    model = OLS(y, x).fit()
    residuals = model.resid
    
    return pd.Series(residuals, index=series.index)

def difference_series(series: pd.Series, order: int = 1) -> pd.Series:
    """
    Apply differencing to a series.
    
    Args:
        series: Input time series
        order: Order of differencing
        
    Returns:
        Differenced series
    """
    return series.diff(order).dropna()

def preprocess_series(
    series: pd.Series,
    max_differencing: int = 3,
    log_counts: bool = True
) -> Dict[str, Any]:
    """
    Preprocess a single time series: handle missing values, check stationarity,
    and apply differencing or detrending as needed.
    
    Args:
        series: Input time series
        max_differencing: Maximum number of differencing operations allowed
        log_counts: Whether to log the number of differencing steps
        
    Returns:
        Dictionary containing:
            - 'processed_series': The preprocessed series
            - 'is_stationary': Whether the series is stationary
            - 'differencing_count': Number of differencing steps applied
            - 'detrended': Whether detrending was applied instead of differencing
            - 'original_length': Length of the original series
            - 'processed_length': Length of the processed series
            - 'adf_p_value': Final ADF p-value
    """
    logger = logging.getLogger(__name__)
    
    # Handle missing values
    processed = interpolate_missing(series)
    
    # Check for minimum length
    if len(processed) < 25:
        logger.warning(f"Series has {len(processed)} points, skipping (Edge Case 1)")
        return {
            'processed_series': processed,
            'is_stationary': False,
            'differencing_count': 0,
            'detrended': False,
            'original_length': len(series),
            'processed_length': len(processed),
            'adf_p_value': None,
            'skipped': True
        }
    
    differencing_count = 0
    detrended = False
    original_processed = processed.copy()
    
    # Check stationarity and apply transformations
    while differencing_count < max_differencing:
        is_stationary, p_value = check_stationarity_adf(processed)
        
        if is_stationary:
            # Series is stationary, try detrending
            try:
                detrended_series = detrend_linear(processed)
                is_detrended_stationary, _ = check_stationarity_adf(detrended_series)
                
                if is_detrended_stationary:
                    processed = detrended_series
                    detrended = True
                    logger.info(f"Series detrended successfully (Edge Case 2: detrending applied)")
                    break
                else:
                    # Detrending didn't work, continue with differencing
                    logger.info("Detrending did not achieve stationarity, continuing with differencing")
            except Exception as e:
                logger.warning(f"Detrending failed: {e}, continuing with differencing")
        
        # Apply differencing
        processed = difference_series(processed)
        differencing_count += 1
        
        if len(processed) < 25:
            logger.warning(f"Series dropped below 25 points after differencing (Edge Case 1)")
            break
    
    # Final stationarity check
    if len(processed) >= 25:
        final_stationary, final_p_value = check_stationarity_adf(processed)
    else:
        final_stationary = False
        final_p_value = None
    
    # Log edge case for unit roots that cannot be detrended (Edge Case 2)
    if not final_stationary and differencing_count >= max_differencing:
        logger.error(
            f"Unit root detected that could not be resolved after {max_differencing} "
            f"differencing steps. Series length: {len(processed)}. "
            f"Final ADF p-value: {final_p_value}. (Edge Case 2)"
        )
    elif not detrended and not final_stationary and differencing_count > 0:
        logger.info(
            f"Series required {differencing_count} differencing steps to attempt stationarity. "
            f"Final status: {'Stationary' if final_stationary else 'Non-stationary'}. "
            f"Final ADF p-value: {final_p_value}. (Edge Case 2: logged differencing count)"
        )
    
    result = {
        'processed_series': processed,
        'is_stationary': final_stationary,
        'differencing_count': differencing_count,
        'detrended': detrended,
        'original_length': len(series),
        'processed_length': len(processed),
        'adf_p_value': final_p_value,
        'skipped': len(processed) < 25
    }
    
    return result

def preprocess_dataset(
    dataset: pd.DataFrame,
    time_column: str = 'datetime',
    value_column: str = 'value',
    max_differencing: int = 3
) -> pd.DataFrame:
    """
    Preprocess an entire dataset (multiple time series).
    
    Args:
        dataset: DataFrame with time series data
        time_column: Name of the time column
        value_column: Name of the value column
        max_differencing: Maximum differencing steps per series
        
    Returns:
        Preprocessed DataFrame
    """
    logger = logging.getLogger(__name__)
    
    # Group by series identifier if present, otherwise treat as single series
    if 'series_id' in dataset.columns:
        groups = dataset.groupby('series_id')
    else:
        groups = [(None, dataset)]
    
    processed_dfs = []
    edge_case_logs = []
    
    for series_id, group in groups:
        series = group.set_index(time_column)[value_column]
        result = preprocess_series(series, max_differencing)
        
        if result['skipped']:
            logger.warning(f"Series {series_id} skipped due to insufficient length")
            edge_case_logs.append({
                'series_id': series_id,
                'reason': 'insufficient_length',
                'length': result['original_length']
            })
            continue
        
        processed_df = pd.DataFrame({
            time_column: result['processed_series'].index,
            value_column: result['processed_series'].values,
            'is_stationary': result['is_stationary'],
            'differencing_count': result['differencing_count'],
            'detrended': result['detrended']
        })
        
        if series_id is not None:
            processed_df['series_id'] = series_id
        
        processed_dfs.append(processed_df)
        
        # Log edge case details for unit roots
        if not result['is_stationary'] and result['differencing_count'] >= max_differencing:
            edge_case_logs.append({
                'series_id': series_id,
                'reason': 'unit_root_undetermined',
                'differencing_count': result['differencing_count'],
                'final_adf_p_value': result['adf_p_value'],
                'processed_length': result['processed_length']
            })
            logger.warning(
                f"Edge Case 2: Series {series_id} has undetermined unit root. "
                f"Differencing count: {result['differencing_count']}, "
                f"Final ADF p-value: {result['adf_p_value']}"
            )
    
    if not processed_dfs:
        return pd.DataFrame()
    
    result_df = pd.concat(processed_dfs, ignore_index=True)
    
    # Log all edge cases encountered
    if edge_case_logs:
        logger.info(f"Encountered {len(edge_case_logs)} edge cases during preprocessing")
        for log in edge_case_logs:
            logger.debug(f"Edge case detail: {log}")
    
    return result_df

def interpolate_missing_values(series: pd.Series) -> pd.Series:
    """
    Alias for interpolate_missing for backward compatibility.
    
    Args:
        series: Input time series
        
    Returns:
        Series with missing values interpolated
    """
    return interpolate_missing(series)
