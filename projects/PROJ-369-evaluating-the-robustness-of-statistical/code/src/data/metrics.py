"""
Metrics computation module for real time series data.

Computes ACF (lag 20), Hurst exponent (via DFA), and spectral density peak ratio
for every REAL loaded series. Does NOT include synthetic series (see T023).
"""
import numpy as np
import pandas as pd
from scipy import signal
from scipy.stats import linregress
from typing import Dict, Any, List, Optional, Tuple
import logging
import os
from pathlib import Path

from src.utils.config import get_path

logger = logging.getLogger(__name__)

# Constants
MAX_LAG_ACF = 20
DFA_MIN_N = 16  # Minimum points for DFA
DFA_SCALE_FACTOR = 0.5  # Start scale at 50% of data length


def compute_acf_lag20(series: pd.Series) -> Dict[str, Any]:
    """
    Compute Autocorrelation Function up to lag 20.
    
    Args:
        series: Input time series (pandas Series with numeric values)
        
    Returns:
        Dictionary containing:
            - acf_values: numpy array of ACF values for lags 0-20
            - max_acf_lag1: ACF at lag 1 (for exclusion in regression)
            - max_acf_absolute: Maximum absolute ACF value (excluding lag 0)
            - max_acf_lag: Lag at which max absolute ACF occurs
    """
    if len(series) < 2:
        raise ValueError("Series must have at least 2 points for ACF computation")
    
    # Compute ACF using numpy's correlate for efficiency
    n = len(series)
    mean = np.mean(series)
    var = np.var(series)
    
    if var == 0:
        # Constant series
        acf_values = np.zeros(MAX_LAG_ACF + 1)
        acf_values[0] = 1.0
    else:
        # Normalize the series
        normalized = (series - mean) / np.sqrt(var)
        
        # Compute ACF using correlation
        acf_values = np.correlate(normalized, normalized, mode='full')
        acf_values = acf_values[n-1:n+MAX_LAG_ACF] / n
        
        # Ensure acf[0] = 1.0
        acf_values[0] = 1.0
    
    max_acf_lag1 = acf_values[1] if len(acf_values) > 1 else 0.0
    
    # Find max absolute ACF (excluding lag 0)
    acf_lags = acf_values[1:]
    max_acf_absolute = np.max(np.abs(acf_lags))
    max_acf_lag = np.argmax(np.abs(acf_lags)) + 1
    
    return {
        'acf_values': acf_values,
        'max_acf_lag1': max_acf_lag1,
        'max_acf_absolute': max_acf_absolute,
        'max_acf_lag': max_acf_lag
    }


def compute_dfa_hurst(series: pd.Series, scales: Optional[List[int]] = None) -> Dict[str, Any]:
    """
    Compute Hurst exponent using Detrended Fluctuation Analysis (DFA).
    
    Args:
        series: Input time series
        scales: Optional list of window sizes to use. If None, uses log-spaced scales.
        
    Returns:
        Dictionary containing:
            - hurst_exponent: Estimated Hurst exponent
            - fluctuation_values: Fluctuation values for each scale
            - scales: Window sizes used
            - r_squared: R-squared of the log-log fit
    """
    n = len(series)
    
    if n < DFA_MIN_N:
        raise ValueError(f"Series length {n} is too short for DFA (minimum {DFA_MIN_N})")
    
    # Generate scales if not provided
    if scales is None:
        min_scale = max(4, int(n * DFA_SCALE_FACTOR / 10))
        max_scale = int(n * 0.9)
        scales = [int(s) for s in np.logspace(np.log10(min_scale), np.log10(max_scale), 10)]
        scales = [s for s in scales if s >= 4]
    
    # Ensure scales are valid
    scales = [s for s in scales if 4 <= s < n]
    if len(scales) < 2:
        raise ValueError("Not enough valid scales for DFA")
    
    # Cumulative sum (profile)
    y = np.cumsum(series - np.mean(series))
    
    fluctuation_values = []
    valid_scales = []
    
    for scale in scales:
        # Divide into non-overlapping windows
        n_windows = n // scale
        if n_windows < 2:
            continue
        
        fluct = []
        
        for i in range(n_windows):
            start = i * scale
            end = start + scale
            window = y[start:end]
            
            # Fit linear trend
            x = np.arange(scale)
            coeffs = np.polyfit(x, window, 1)
            trend = np.polyval(coeffs, x)
            
            # Detrend
            detrended = window - trend
            fluct.append(np.sqrt(np.mean(detrended ** 2)))
        
        if fluct:
            F = np.mean(fluct)
            if F > 0:
                fluctuation_values.append(F)
                valid_scales.append(scale)
    
    if len(valid_scales) < 2:
        raise ValueError("Not enough valid fluctuation values for DFA")
    
    # Fit log-log relationship
    log_scales = np.log(valid_scales)
    log_fluct = np.log(fluctuation_values)
    
    slope, intercept, r_value, p_value, std_err = linregress(log_scales, log_fluct)
    
    return {
        'hurst_exponent': slope,
        'fluctuation_values': np.array(fluctuation_values),
        'scales': np.array(valid_scales),
        'r_squared': r_value ** 2
    }


def compute_spectral_density_peak_ratio(series: pd.Series) -> Dict[str, Any]:
    """
    Compute spectral density and peak ratio metric.
    
    The peak ratio is the ratio of the maximum spectral density (excluding DC)
    to the median spectral density, indicating the presence of strong periodic components.
    
    Args:
        series: Input time series
        
    Returns:
        Dictionary containing:
            - peak_ratio: Ratio of max to median spectral density
            - peak_frequency: Frequency at which peak occurs
            - spectral_density: Full spectral density array
            - frequencies: Frequency array
    """
    n = len(series)
    if n < 4:
        raise ValueError("Series must have at least 4 points for spectral analysis")
    
    # Compute PSD using Welch's method
    nperseg = min(256, n // 2)
    if nperseg < 2:
        nperseg = 2
    
    freqs, psd = signal.welch(
        series, 
        fs=1.0,  # Normalized frequency
        nperseg=nperseg,
        window='hann',
        scaling='density'
    )
    
    # Exclude DC component (index 0)
    if len(psd) > 1:
        psd_non_dc = psd[1:]
        freqs_non_dc = freqs[1:]
        
        if len(psd_non_dc) > 0:
            max_psd = np.max(psd_non_dc)
            median_psd = np.median(psd_non_dc)
            
            if median_psd > 0:
                peak_ratio = max_psd / median_psd
            else:
                peak_ratio = np.inf
            
            peak_idx = np.argmax(psd_non_dc)
            peak_frequency = freqs_non_dc[peak_idx]
        else:
            peak_ratio = 0.0
            peak_frequency = 0.0
    else:
        peak_ratio = 0.0
        peak_frequency = 0.0
    
    return {
        'peak_ratio': peak_ratio,
        'peak_frequency': peak_frequency,
        'spectral_density': psd,
        'frequencies': freqs
    }


def compute_all_metrics(series: pd.Series, series_name: str = "unknown") -> Dict[str, Any]:
    """
    Compute all metrics for a single series.
    
    Args:
        series: Input time series
        series_name: Name/identifier for the series
        
    Returns:
        Dictionary containing all computed metrics
    """
    logger.info(f"Computing metrics for series: {series_name} (length: {len(series)})")
    
    result = {
        'series_name': series_name,
        'series_length': len(series),
        'status': 'success'
    }
    
    try:
        # ACF
        acf_result = compute_acf_lag20(series)
        result['acf'] = {
            'lag_20_values': acf_result['acf_values'].tolist(),
            'max_acf_lag1': acf_result['max_acf_lag1'],
            'max_acf_absolute': acf_result['max_acf_absolute'],
            'max_acf_lag': acf_result['max_acf_lag']
        }
        
        # DFA Hurst
        dfa_result = compute_dfa_hurst(series)
        result['hurst'] = {
            'exponent': dfa_result['hurst_exponent'],
            'r_squared': dfa_result['r_squared'],
            'n_scales': len(dfa_result['scales'])
        }
        
        # Spectral density
        spec_result = compute_spectral_density_peak_ratio(series)
        result['spectral'] = {
            'peak_ratio': spec_result['peak_ratio'],
            'peak_frequency': spec_result['peak_frequency']
        }
        
    except Exception as e:
        logger.error(f"Error computing metrics for {series_name}: {str(e)}")
        result['status'] = 'failed'
        result['error'] = str(e)
    
    return result


def compute_metrics_for_all_real_series(
    data_dir: Optional[str] = None,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Compute metrics for all real loaded series in the data directory.
    
    This function processes ONLY real data series (not synthetic) as per T014.
    
    Args:
        data_dir: Directory containing processed real data. If None, uses default path.
        output_path: Path to save results CSV. If None, results are returned as DataFrame.
        
    Returns:
        DataFrame with metrics for all series
    """
    if data_dir is None:
        data_dir = get_path('data_processed')
    
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_path}")
    
    # Find all CSV files (processed real data)
    csv_files = list(data_path.glob('*.csv'))
    
    if not csv_files:
        logger.warning(f"No CSV files found in {data_path}")
        return pd.DataFrame()
    
    logger.info(f"Found {len(csv_files)} real data series to process")
    
    all_results = []
    
    for csv_file in csv_files:
        try:
            logger.info(f"Processing: {csv_file.name}")
            
            # Load the series
            df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
            
            # Handle different formats
            if df.shape[1] == 1:
                # Single column
                series = df.iloc[:, 0]
            elif 'value' in df.columns:
                series = df['value']
            else:
                # Take first numeric column
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    series = df[numeric_cols[0]]
                else:
                    logger.warning(f"No numeric data in {csv_file.name}, skipping")
                    continue
            
            # Drop NaN values
            series = series.dropna()
            
            if len(series) < DFA_MIN_N:
                logger.warning(f"Series {csv_file.name} too short ({len(series)} < {DFA_MIN_N}), skipping")
                continue
            
            # Compute metrics
            metrics = compute_all_metrics(series, series_name=csv_file.stem)
            all_results.append(metrics)
            
        except Exception as e:
            logger.error(f"Failed to process {csv_file.name}: {str(e)}")
            all_results.append({
                'series_name': csv_file.stem,
                'status': 'failed',
                'error': str(e)
            })
    
    # Convert to DataFrame
    if not all_results:
        return pd.DataFrame()
    
    # Flatten the nested dictionaries
    records = []
    for result in all_results:
        record = {
            'series_name': result.get('series_name', 'unknown'),
            'series_length': result.get('series_length', 0),
            'status': result.get('status', 'unknown'),
        }
        
        if result.get('status') == 'success':
            # ACF metrics
            acf = result.get('acf', {})
            record['max_acf_lag1'] = acf.get('max_acf_lag1', 0.0)
            record['max_acf_absolute'] = acf.get('max_acf_absolute', 0.0)
            record['max_acf_lag'] = acf.get('max_acf_lag', 0)
            
            # Hurst metrics
            hurst = result.get('hurst', {})
            record['hurst_exponent'] = hurst.get('exponent', 0.0)
            record['hurst_r_squared'] = hurst.get('r_squared', 0.0)
            
            # Spectral metrics
            spectral = result.get('spectral', {})
            record['spectral_peak_ratio'] = spectral.get('peak_ratio', 0.0)
            record['spectral_peak_frequency'] = spectral.get('peak_frequency', 0.0)
        else:
            record['error'] = result.get('error', 'Unknown error')
        
        records.append(record)
    
    df_results = pd.DataFrame(records)
    
    # Save to output if specified
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df_results.to_csv(output_file, index=False)
        logger.info(f"Results saved to {output_file}")
    
    return df_results


def main():
    """Main entry point for computing metrics on real data."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Define output path
    output_path = get_path('data_metrics_real')
    
    logger.info("Starting metrics computation for all real series...")
    
    try:
        df_metrics = compute_metrics_for_all_real_series(
            data_dir=None,
            output_path=output_path
        )
        
        if len(df_metrics) > 0:
            logger.info(f"Successfully computed metrics for {len(df_metrics)} series")
            logger.info(f"Results saved to: {output_path}")
            print(f"\nMetrics Summary:")
            print(df_metrics[['series_name', 'status', 'hurst_exponent', 'spectral_peak_ratio']].to_string())
        else:
            logger.warning("No metrics computed (no valid series found)")
            
    except Exception as e:
        logger.error(f"Failed to compute metrics: {str(e)}")
        raise


if __name__ == "__main__":
    main()
