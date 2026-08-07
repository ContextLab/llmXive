import logging
import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import linregress
from scipy import signal
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

def handle_missing_values(series: pd.Series, method: str = "linear") -> pd.Series:
    """
    Handle missing values in a time series using linear interpolation.
    
    Args:
        series: Input pandas Series with potential NaN values
        method: Interpolation method (default: "linear")
        
    Returns:
        Series with missing values filled
        
    Raises:
        ValueError: If series has too many missing values to interpolate
    """
    if series.isna().all():
        raise ValueError("Cannot interpolate: series is entirely NaN")
        
    filled_series = series.interpolate(method=method)
    
    # Check if any NaNs remain at edges
    if filled_series.isna().any():
        # Forward fill remaining NaNs at start, backward fill at end
        filled_series = filled_series.ffill().bfill()
        
        if filled_series.isna().any():
            raise ValueError("Could not fill all missing values in series")
            
    return filled_series

def check_stationarity_adf(series: pd.Series, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Check stationarity using Augmented Dickey-Fuller test.
    
    Args:
        series: Input time series
        alpha: Significance level for the test
        
    Returns:
        Dictionary with test results
    """
    try:
        adf_result = stats.adfuller(series.dropna(), autolag='AIC')
        return {
            'adf_statistic': adf_result[0],
            'p_value': adf_result[1],
            'critical_values': adf_result[4],
            'is_stationary': adf_result[1] < alpha,
            'p_value_threshold': alpha
        }
    except Exception as e:
        logger.error(f"ADF test failed: {e}")
        return {
            'adf_statistic': None,
            'p_value': None,
            'critical_values': None,
            'is_stationary': False,
            'error': str(e),
            'p_value_threshold': alpha
        }

def make_stationary(series: pd.Series, max_diff_order: int = 3) -> Tuple[pd.Series, Dict[str, Any]]:
    """
    Make a series stationary by differencing or detrending.
    
    Args:
        series: Input time series
        max_diff_order: Maximum number of differences to apply
        
    Returns:
        Tuple of (stationary_series, processing_info)
    """
    info = {
        'original_length': len(series),
        'diff_orders_applied': 0,
        'method': None,
        'is_stationary': False
    }
    
    current_series = series.copy()
    
    # First try ADF test
    adf_info = check_stationarity_adf(current_series)
    
    if adf_info['is_stationary']:
        info['method'] = 'already_stationary'
        info['is_stationary'] = True
        info['adf_p_value'] = adf_info['p_value']
        return current_series, info
    
    # Try differencing
    for order in range(1, max_diff_order + 1):
        current_series = current_series.diff().dropna()
        info['diff_orders_applied'] = order
        
        if len(current_series) < 25:
            logger.warning(f"Series too short after {order} differencing operations: {len(current_series)} points")
            break
            
        adf_info = check_stationarity_adf(current_series)
        
        if adf_info['is_stationary']:
            info['method'] = 'differencing'
            info['is_stationary'] = True
            info['adf_p_value'] = adf_info['p_value']
            return current_series, info
    
    # If differencing didn't work, try detrending
    if len(current_series) >= 25:
        logger.info("Differencing failed to achieve stationarity, attempting detrending")
        
        # Linear detrending
        x = np.arange(len(current_series))
        slope, intercept, r_value, p_value, std_err = linregress(x, current_series)
        trend = intercept + slope * x
        detrended = current_series - trend
        
        adf_info = check_stationarity_adf(detrended)
        
        if adf_info['is_stationary']:
            info['method'] = 'detrending'
            info['is_stationary'] = True
            info['adf_p_value'] = adf_info['p_value']
            info['detrend_slope'] = slope
            return detrended, info
        
        logger.warning(f"Detrending also failed to achieve stationarity (p={adf_info['p_value']})")
    
    info['method'] = 'failed'
    info['is_stationary'] = False
    return current_series, info

def resample_uk_load_data(series: pd.Series, freq: str = "H") -> pd.Series:
    """
    Resample UK National Grid Load data to a consistent frequency.
    
    Args:
        series: Input time series (should have datetime index)
        freq: Target frequency (default: "H" for hourly)
        
    Returns:
        Resampled series
    """
    if not isinstance(series.index, pd.DatetimeIndex):
        logger.warning("Series does not have DatetimeIndex, cannot resample")
        return series
        
    resampled = series.resample(freq).mean()
    # Fill any resulting NaNs from resampling
    resampled = resampled.interpolate(method='linear').ffill().bfill()
    
    return resampled

def process_series_for_stationarity(series: pd.Series, min_points: int = 25) -> Tuple[Optional[pd.Series], Dict[str, Any]]:
    """
    Process a single series for stationarity with edge case handling.
    
    Args:
        series: Input time series
        min_points: Minimum number of points required (default: 25)
        
    Returns:
        Tuple of (processed_series or None, processing_info)
    """
    info = {
        'original_length': len(series),
        'skipped': False,
        'skip_reason': None,
        'final_length': None,
        'stationarity_info': None
    }
    
    # Edge case: Skip datasets < 25 points
    if len(series) < min_points:
        logger.warning(f"Skipping series with {len(series)} points (minimum: {min_points})")
        info['skipped'] = True
        info['skip_reason'] = f"Series too short: {len(series)} < {min_points} points"
        return None, info
    
    # Handle missing values first
    try:
        clean_series = handle_missing_values(series)
    except ValueError as e:
        logger.error(f"Failed to handle missing values: {e}")
        info['skipped'] = True
        info['skip_reason'] = f"Missing value handling failed: {e}"
        return None, info
        
    info['final_length'] = len(clean_series)
    
    # Make stationary
    stationary_series, stationarity_info = make_stationary(clean_series)
    info['stationarity_info'] = stationarity_info
    
    # Final check: ensure we still have enough points after processing
    if len(stationary_series) < min_points:
        logger.warning(f"Series dropped below {min_points} points after stationarity processing: {len(stationary_series)}")
        info['skipped'] = True
        info['skip_reason'] = f"Series too short after processing: {len(stationary_series)} < {min_points} points"
        return None, info
        
    return stationary_series, info

def preprocess_dataset(dataset: Dict[str, Any], min_points: int = 25) -> Dict[str, Any]:
    """
    Preprocess a complete dataset (multiple series).
    
    Args:
        dataset: Dictionary containing 'series' key with list of series data
        min_points: Minimum points required per series
        
    Returns:
        Processed dataset with metadata
    """
    processed_series_list = []
    processing_log = []
    
    for i, series_data in enumerate(dataset.get('series', [])):
        series = series_data.get('data')
        series_name = series_data.get('name', f'Series_{i}')
        
        if series is None:
            logger.warning(f"Skipping series {series_name}: no data found")
            continue
            
        processed_series, info = process_series_for_stationarity(series, min_points)
        
        processing_entry = {
            'name': series_name,
            'original_length': info['original_length'],
            'skipped': info['skipped'],
            'skip_reason': info['skip_reason'],
            'final_length': info['final_length'],
            'stationarity_method': info.get('stationarity_info', {}).get('method'),
            'is_stationary': info.get('stationarity_info', {}).get('is_stationary'),
            'adf_p_value': info.get('stationarity_info', {}).get('adf_p_value')
        }
        processing_log.append(processing_entry)
        
        if processed_series is not None:
            processed_series_list.append({
                'name': series_name,
                'data': processed_series
            })
    
    return {
        'processed_series': processed_series_list,
        'processing_log': processing_log,
        'total_series': len(dataset.get('series', [])),
        'processed_count': len(processed_series_list),
        'skipped_count': sum(1 for log in processing_log if log['skipped'])
    }

def compute_spectral_density_with_fallback(series: pd.Series, max_lag: int = 20) -> Dict[str, Any]:
    """
    Compute spectral density with fallback to variance for numerical instability.
    
    Args:
        series: Input time series
        max_lag: Maximum lag for spectral analysis
        
    Returns:
        Dictionary with spectral density metrics or fallback variance
    """
    try:
        # Ensure series is numeric and clean
        clean_series = series.dropna()
        if len(clean_series) < 10:
            logger.warning("Series too short for spectral density calculation")
            return {
                'method': 'fallback_variance',
                'variance': float(series.var()),
                'peak_ratio': None,
                'peak_frequency': None,
                'success': False
            }
        
        # Compute spectral density using Welch's method
        freqs, psd = signal.welch(clean_series, fs=1.0, nperseg=min(256, len(clean_series)))
        
        if len(psd) == 0 or np.any(np.isnan(psd)) or np.any(np.isinf(psd)):
            raise ValueError("Invalid spectral density output")
        
        # Calculate peak ratio (max PSD / mean PSD)
        mean_psd = np.mean(psd)
        if mean_psd == 0:
            raise ValueError("Mean PSD is zero, cannot compute ratio")
            
        max_psd = np.max(psd)
        peak_ratio = max_psd / mean_psd
        
        # Find peak frequency
        peak_idx = np.argmax(psd)
        peak_freq = freqs[peak_idx]
        
        # Check for numerical instability
        if np.isnan(peak_ratio) or np.isinf(peak_ratio) or peak_ratio > 1e6:
            logger.warning(f"Spectral density peak ratio {peak_ratio} indicates numerical instability, using variance fallback")
            return {
                'method': 'fallback_variance',
                'variance': float(clean_series.var()),
                'peak_ratio': None,
                'peak_frequency': None,
                'success': False,
                'warning': f"Peak ratio {peak_ratio} exceeds stability threshold"
            }
        
        return {
            'method': 'spectral_density',
            'peak_ratio': float(peak_ratio),
            'peak_frequency': float(peak_freq),
            'mean_psd': float(mean_psd),
            'max_psd': float(max_psd),
            'success': True
        }
        
    except Exception as e:
        logger.warning(f"Spectral density calculation failed: {e}, using variance fallback")
        return {
            'method': 'fallback_variance',
            'variance': float(series.var()),
            'peak_ratio': None,
            'peak_frequency': None,
            'success': False,
            'error': str(e)
        }

def compute_acf_lag20(series: pd.Series, max_lag: int = 20) -> Dict[str, Any]:
    """
    Compute ACF up to lag 20 with edge case handling.
    
    Args:
        series: Input time series
        max_lag: Maximum lag (default: 20)
        
    Returns:
        Dictionary with ACF values
    """
    try:
        clean_series = series.dropna()
        if len(clean_series) < max_lag + 10:
            logger.warning(f"Series too short for ACF at lag {max_lag}: {len(clean_series)} points")
            return {
                'acf_values': None,
                'max_acf_lag1': None,
                'max_acf_value': None,
                'success': False,
                'warning': f"Series too short: {len(clean_series)} < {max_lag + 10} points"
            }
        
        acf_values = stats.acf(clean_series, nlags=max_lag, fft=False)
        
        return {
            'acf_values': acf_values.tolist(),
            'max_acf_lag1': float(acf_values[1]) if len(acf_values) > 1 else None,
            'max_acf_value': float(np.max(np.abs(acf_values[1:]))) if len(acf_values) > 1 else None,
            'success': True
        }
    except Exception as e:
        logger.error(f"ACF calculation failed: {e}")
        return {
            'acf_values': None,
            'max_acf_lag1': None,
            'max_acf_value': None,
            'success': False,
            'error': str(e)
        }

def compute_dfa_hurst(series: pd.Series) -> Dict[str, Any]:
    """
    Compute Hurst exponent using DFA with edge case handling.
    
    Args:
        series: Input time series
        
    Returns:
        Dictionary with Hurst exponent
    """
    try:
        clean_series = series.dropna()
        if len(clean_series) < 50:
            logger.warning(f"Series too short for DFA: {len(clean_series)} points")
            return {
                'hurst_exponent': None,
                'success': False,
                'warning': f"Series too short: {len(clean_series)} < 50 points"
            }
        
        # Simplified DFA implementation
        n = len(clean_series)
        # Integrate the series (remove mean first)
        y = np.cumsum(clean_series - np.mean(clean_series))
        
        # Define window sizes
        window_sizes = [int(n/4), int(n/2), int(3*n/4)]
        window_sizes = [w for w in window_sizes if w > 10]
        
        if len(window_sizes) < 2:
            return {
                'hurst_exponent': None,
                'success': False,
                'warning': "Not enough window sizes for DFA"
            }
        
        rms_values = []
        for window in window_sizes:
            # Split into segments
            segments = n // window
            rms = 0
            for seg in range(segments):
                start = seg * window
                end = start + window
                segment = y[start:end]
                
                # Detrend segment
                x_local = np.arange(window)
                slope, intercept, _, _, _ = linregress(x_local, segment)
                trend = intercept + slope * x_local
                detrended = segment - trend
                
                rms += np.sqrt(np.mean(detrended**2))
            
            rms_values.append(np.sqrt(rms / segments))
        
        # Fit line in log-log space
        log_windows = np.log(window_sizes)
        log_rms = np.log(rms_values)
        slope, intercept, r_value, p_value, std_err = linregress(log_windows, log_rms)
        
        hurst = slope
        
        # Validate Hurst exponent
        if not (0 < hurst < 1) or np.isnan(hurst) or np.isinf(hurst):
            logger.warning(f"Invalid Hurst exponent: {hurst}")
            return {
                'hurst_exponent': None,
                'success': False,
                'warning': f"Invalid Hurst exponent: {hurst}"
            }
        
        return {
            'hurst_exponent': float(hurst),
            'r_squared': float(r_value**2),
            'success': True
        }
    except Exception as e:
        logger.error(f"DFA Hurst calculation failed: {e}")
        return {
            'hurst_exponent': None,
            'success': False,
            'error': str(e)
        }

def compute_spectral_density_peak_ratio(series: pd.Series) -> Dict[str, Any]:
    """
    Compute spectral density peak ratio with fallback to variance.
    
    Args:
        series: Input time series
        
    Returns:
        Dictionary with spectral density metrics
    """
    return compute_spectral_density_with_fallback(series)

def compute_all_metrics(series: pd.Series) -> Dict[str, Any]:
    """
    Compute all metrics for a series with edge case handling.
    
    Args:
        series: Input time series
        
    Returns:
        Dictionary with all computed metrics
    """
    acf_result = compute_acf_lag20(series)
    hurst_result = compute_dfa_hurst(series)
    spectral_result = compute_spectral_density_peak_ratio(series)
    
    return {
        'acf': acf_result,
        'hurst': hurst_result,
        'spectral_density': spectral_result,
        'all_success': acf_result['success'] and hurst_result['success'] and spectral_result['success']
    }

def compute_metrics_for_all_real_series(real_series_list: list) -> list:
    """
    Compute metrics for all real series in a list.
    
    Args:
        real_series_list: List of dictionaries with 'name' and 'data' keys
        
    Returns:
        List of metric dictionaries
    """
    results = []
    
    for series_data in real_series_list:
        name = series_data.get('name', 'Unknown')
        series = series_data.get('data')
        
        if series is None:
            logger.warning(f"Skipping {name}: no data found")
            continue
            
        metrics = compute_all_metrics(series)
        metrics['name'] = name
        results.append(metrics)
        
    return results

def main():
    """Main function for preprocessing module."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Preprocessing module loaded successfully")
    logger.info("Edge case handling implemented:")
    logger.info("  - Skip datasets < 25 points with warning")
    logger.info("  - Fallback to variance metric for spectral density instability")

if __name__ == "__main__":
    main()