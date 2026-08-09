import numpy as np
import pandas as pd
from scipy import signal
from scipy.stats import linregress
from typing import Dict, Any, Union, List, Optional
import logging

logger = logging.getLogger(__name__)

class MetricsError(Exception):
    """Custom exception for metrics computation errors."""
    pass

def compute_acf_lag(series: Union[pd.Series, np.ndarray], max_lag: int = 10) -> Dict[int, float]:
    """
    Compute Autocorrelation Function (ACF) up to max_lag.
    
    Args:
        series: Input time series
        max_lag: Maximum lag to compute ACF for
        
    Returns:
        Dictionary mapping lag to ACF value
    """
    if isinstance(series, pd.Series):
        series = series.values
    
    n = len(series)
    if n < max_lag + 10:
        logger.warning(f"Series length {n} is too short for max_lag {max_lag}")
        max_lag = max(1, n - 10)
    
    acf_vals = signal.correlate(series - np.mean(series), series - np.mean(series), mode='full')
    acf_vals = acf_vals[n-1:] / acf_vals[n-1]  # Normalize by lag 0
    
    return {lag: float(acf_vals[lag]) for lag in range(min(max_lag + 1, len(acf_vals)))}

def compute_dfa_hurst(series: Union[pd.Series, np.ndarray], min_scale: int = 10, max_scale: int = None) -> float:
    """
    Compute Hurst exponent using Detrended Fluctuation Analysis (DFA).
    
    Note: This is for estimation only. The spec mandates linear regression residuals
    for detrending stationary series, but DFA is used here for Hurst estimation.
    
    Args:
        series: Input time series
        min_scale: Minimum window size for DFA
        max_scale: Maximum window size for DFA
        
    Returns:
        Estimated Hurst exponent
    """
    if isinstance(series, pd.Series):
        series = series.values
    
    n = len(series)
    if max_scale is None:
        max_scale = n // 4
    
    if min_scale >= max_scale:
        raise MetricsError(f"min_scale ({min_scale}) must be less than max_scale ({max_scale})")
    
    # Integrate the series
    Y = np.cumsum(series - np.mean(series))
    
    scales = np.logspace(np.log10(min_scale), np.log10(max_scale), num=10, dtype=int)
    fluctuation = []
    
    for scale in scales:
        # Divide into segments
        n_segments = n // scale
        if n_segments < 2:
            continue
        
        fluct_vals = []
        for seg_idx in range(n_segments):
            start = seg_idx * scale
            end = start + scale
            y_seg = Y[start:end]
            x_seg = np.arange(scale)
            
            # Fit linear trend
            try:
                slope, intercept, _, _, _ = linregress(x_seg, y_seg)
                trend = slope * x_seg + intercept
                residual = y_seg - trend
                fluct_vals.append(np.sqrt(np.mean(residual**2)))
            except:
                continue
        
        if fluct_vals:
            fluctuation.append(np.mean(fluct_vals))
    
    if len(fluctuation) < 2:
        logger.warning("Not enough scales for DFA")
        return 0.5
    
    # Fit log-log relationship
    log_scales = np.log(scales[:len(fluctuation)])
    log_fluct = np.log(fluctuation)
    
    try:
        slope, _, _, _, _ = linregress(log_scales, log_fluct)
        return float(slope)
    except:
        return 0.5

def compute_spectral_peak_ratio(series: Union[pd.Series, np.ndarray], min_frequency: float = 0.01) -> Optional[float]:
    """
    Compute spectral density peak ratio to detect periodicity.
    
    Args:
        series: Input time series
        min_frequency: Minimum frequency to consider
        
    Returns:
        Ratio of peak spectral density to median spectral density, or None if computation fails
    """
    if isinstance(series, pd.Series):
        series = series.values
    
    n = len(series)
    if n < 10:
        logger.warning("Series too short for spectral analysis")
        return None
    
    try:
        # Compute periodogram
        freqs, psd = signal.periodogram(series, fs=1.0, scaling='density')
        
        # Filter out very low frequencies
        valid_mask = freqs >= min_frequency
        if not np.any(valid_mask):
            logger.warning("No valid frequencies above min_frequency")
            return None
        
        valid_freqs = freqs[valid_mask]
        valid_psd = psd[valid_mask]
        
        if len(valid_psd) < 3:
            logger.warning("Too few frequency points for spectral analysis")
            return None
        
        # Calculate peak ratio
        peak_psd = np.max(valid_psd)
        median_psd = np.median(valid_psd)
        
        if median_psd == 0:
            return None
        
        return float(peak_psd / median_psd)
        
    except Exception as e:
        logger.warning(f"Spectral density computation failed: {e}")
        return None

def compute_all_metrics(series: Union[pd.Series, np.ndarray], max_lag: int = 10, 
                      min_scale: int = 10, max_scale: int = None,
                      min_frequency: float = 0.01) -> Dict[str, Any]:
    """
    Compute all metrics for a time series.
    
    Args:
        series: Input time series
        max_lag: Maximum lag for ACF
        min_scale: Minimum scale for DFA
        max_scale: Maximum scale for DFA
        min_frequency: Minimum frequency for spectral analysis
        
    Returns:
        Dictionary containing all computed metrics
    """
    metrics = {}
    
    # ACF
    try:
        metrics['acf'] = compute_acf_lag(series, max_lag)
        metrics['acf_lag1'] = metrics['acf'].get(1, 0.0)
    except Exception as e:
        logger.error(f"ACF computation failed: {e}")
        metrics['acf'] = {}
        metrics['acf_lag1'] = 0.0
    
    # Hurst (DFA)
    try:
        metrics['hurst'] = compute_dfa_hurst(series, min_scale, max_scale)
    except Exception as e:
        logger.error(f"DFA computation failed: {e}")
        metrics['hurst'] = 0.5
    
    # Spectral Density Peak Ratio
    spectral_ratio = compute_spectral_peak_ratio(series, min_frequency)
    if spectral_ratio is not None:
        metrics['spectral_peak_ratio'] = spectral_ratio
    else:
        # Fallback to variance-based metric if spectral density fails
        logger.info("Spectral density failed, using variance-based fallback")
        if isinstance(series, pd.Series):
            series = series.values
        metrics['spectral_peak_ratio'] = None
        metrics['variance'] = float(np.var(series))
        # Use coefficient of variation as a proxy for spectral complexity
        mean_val = np.mean(series)
        if mean_val != 0:
            metrics['spectral_fallback_cv'] = float(np.std(series) / abs(mean_val))
        else:
            metrics['spectral_fallback_cv'] = float(np.std(series))
    
    return metrics

def compute_metrics_for_dataset(dataset_path: str, dataset_id: str, 
                              max_lag: int = 10, min_scale: int = 10,
                              max_scale: int = None, min_frequency: float = 0.01) -> Dict[str, Any]:
    """
    Compute metrics for a dataset from file.
    
    Args:
        dataset_path: Path to the dataset file
        dataset_id: Identifier for the dataset
        max_lag: Maximum lag for ACF
        min_scale: Minimum scale for DFA
        max_scale: Maximum scale for DFA
        min_frequency: Minimum frequency for spectral analysis
        
    Returns:
        Dictionary containing dataset ID and computed metrics
    """
    try:
        # Load dataset
        if dataset_path.endswith('.csv'):
            df = pd.read_csv(dataset_path, parse_dates=True, index_col=0)
        else:
            raise MetricsError(f"Unsupported file format: {dataset_path}")
        
        # Assume first numeric column is the series
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            raise MetricsError("No numeric columns found in dataset")
        
        series = df[numeric_cols[0]]
        
        # Remove NaN values
        series = series.dropna()
        
        if len(series) < 20:
            logger.warning(f"Dataset {dataset_id} too short after cleaning: {len(series)} points")
            return {
                'dataset_id': dataset_id,
                'error': 'Series too short',
                'metrics': {}
            }
        
        metrics = compute_all_metrics(series, max_lag, min_scale, max_scale, min_frequency)
        
        return {
            'dataset_id': dataset_id,
            'metrics': metrics,
            'series_length': len(series)
        }
        
    except Exception as e:
        logger.error(f"Failed to compute metrics for {dataset_id}: {e}")
        return {
            'dataset_id': dataset_id,
            'error': str(e),
            'metrics': {}
        }