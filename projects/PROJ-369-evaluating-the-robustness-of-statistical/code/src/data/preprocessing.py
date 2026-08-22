import logging
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller
from statsmodels.regression.linear_model import OLS
from src.utils.logging import log_info, log_warning, log_error, log_critical

class PreprocessingError(Exception):
    """Custom exception for preprocessing errors."""
    pass

def interpolate_missing(series: pd.Series, method: str = 'linear') -> pd.Series:
    """
    Interpolate missing values in a time series.
    
    Args:
        series: Input time series
        method: Interpolation method ('linear', 'time', 'index', etc.)
        
    Returns:
        Interpolated series
    """
    if series.isna().all():
        raise PreprocessingError("Series contains only NaN values")
    
    return series.interpolate(method=method).ffill().bfill()

def check_stationarity_adf(series: pd.Series, alpha: float = 0.05) -> dict:
    """
    Check stationarity using Augmented Dickey-Fuller test.
    
    Args:
        series: Input time series
        alpha: Significance level
        
    Returns:
        Dictionary with test results
    """
    if len(series) < 10:
        raise PreprocessingError("Series too short for ADF test")
    
    result = adfuller(series.dropna(), autolag='AIC')
    
    return {
        'stationary': result[1] < alpha,
        'p_value': result[1],
        'adf_statistic': result[0],
        'critical_values': result[4],
        'lags_used': result[2]
    }

def detrend_linear(series: pd.Series) -> pd.Series:
    """
    Detrend series using linear regression residuals.
    
    Args:
        series: Input time series
        
    Returns:
        Residuals from linear regression (detrended series)
    """
    if len(series) < 2:
        raise PreprocessingError("Series too short for linear detrending")
    
    x = np.arange(len(series))
    y = series.values
    
    # Fit linear regression
    model = OLS(y, np.column_stack([np.ones(len(x)), x])).fit()
    residuals = model.resid
    
    return pd.Series(residuals, index=series.index)

def difference_series(series: pd.Series, order: int = 1) -> pd.Series:
    """
    Difference a time series to remove unit roots.
    
    Args:
        series: Input time series
        order: Order of differencing
        
    Returns:
        Differenced series
    """
    return series.diff(order).dropna()

# Maximum differencing limit to prevent infinite loops (T063 enhancement)
MAX_DIFFERENCING_LIMIT = 10

def preprocess_series(series: pd.Series, max_lag: int = 20) -> dict:
    """
    Preprocess a single time series:
    1. Interpolate missing values
    2. Check stationarity (ADF)
    3. If non-stationary: difference until stationary or max limit reached
    4. If stationary: detrend using linear regression residuals
    5. Calculate spectral density peak ratio
    
    Args:
        series: Input time series
        max_lag: Maximum lag for ACF calculation
        
    Returns:
        Dictionary with processed series and metadata
    """
    original_series = series.copy()
    series = interpolate_missing(series)
    
    differencing_count = 0
    stationarity_status = "unknown"
    detrending_status = "not_applicable"
    
    # T063 Enhancement: Maximum differencing limit to prevent infinite loops
    while differencing_count < MAX_DIFFERENCING_LIMIT:
        adf_result = check_stationarity_adf(series)
        
        if adf_result['stationary']:
            stationarity_status = "stationary_after_differencing" if differencing_count > 0 else "already_stationary"
            # Detrend using linear regression residuals
            detrended = detrend_linear(series)
            detrending_status = "detrended"
            series = detrended
            break
        else:
            # Non-stationary, difference the series
            series = difference_series(series, order=1)
            differencing_count += 1
            
            if len(series) < 10:
                log_critical(f"Series became too short after differencing (length={len(series)})")
                stationarity_status = "failed_short_series"
                break
    else:
        # T063 Enhancement: Exceeded maximum differencing limit
        log_critical(f"Series exceeded maximum differencing limit ({MAX_DIFFERENCING_LIMIT}). Unit root cannot be resolved.")
        stationarity_status = "unit_root_failure"
        raise PreprocessingError(
            f"Series failed to achieve stationarity after {MAX_DIFFERENCING_LIMIT} differences. "
            f"Likely contains an unresolvable unit root. Dataset may be unsuitable for analysis."
        )
    
    # Calculate spectral density peak ratio
    try:
        spectral_peak_ratio = compute_spectral_peak_ratio(series)
    except Exception as e:
        log_warning(f"Spectral density calculation failed: {e}. Using variance-based fallback.")
        spectral_peak_ratio = float(np.var(series))
    
    return {
        'processed_series': series,
        'original_series': original_series,
        'stationarity_status': stationarity_status,
        'differencing_count': differencing_count,
        'detrending_status': detrending_status,
        'spectral_density_peak_ratio': spectral_peak_ratio
    }

def preprocess_dataset(dataset: dict, max_lag: int = 20) -> dict:
    """
    Preprocess an entire dataset (multiple series).
    
    Args:
        dataset: Dictionary with 'series' key containing list of series
        max_lag: Maximum lag for ACF calculation
        
    Returns:
        Dictionary with processed datasets and metadata
    """
    processed_datasets = []
    skipped_datasets = []
    
    for series_data in dataset.get('series', []):
        series_id = series_data.get('id', 'unknown')
        series = series_data.get('data')
        
        if series is None or len(series) < 25:
            log_warning(f"Skipping dataset {series_id}: length < 25")
            skipped_datasets.append({
                'id': series_id,
                'reason': 'too_short',
                'length': len(series) if series is not None else 0
            })
            continue
        
        try:
            result = preprocess_series(series, max_lag)
            result['series_id'] = series_id
            processed_datasets.append(result)
        except PreprocessingError as e:
            log_error(f"Preprocessing failed for {series_id}: {e}")
            skipped_datasets.append({
                'id': series_id,
                'reason': 'preprocessing_error',
                'error': str(e)
            })
        except Exception as e:
            log_critical(f"Unexpected error processing {series_id}: {e}")
            skipped_datasets.append({
                'id': series_id,
                'reason': 'unexpected_error',
                'error': str(e)
            })
    
    return {
        'processed': processed_datasets,
        'skipped': skipped_datasets,
        'total': len(dataset.get('series', []))
    }

def compute_spectral_peak_ratio(series: pd.Series) -> float:
    """
    Calculate spectral density peak ratio.
    Ratio of max peak in low-freq band to mean floor in high-freq band.
    
    Args:
        series: Input time series
        
    Returns:
        Spectral peak ratio
    """
    from scipy import signal
    
    # Compute periodogram
    freqs, psd = signal.welch(series, nperseg=min(len(series), 256))
    
    if len(freqs) < 10:
        raise ValueError("Series too short for spectral analysis")
    
    # Low-frequency band (first 10% of frequencies)
    low_freq_idx = int(len(freqs) * 0.1)
    low_freq_psd = psd[:low_freq_idx]
    
    # High-frequency band (last 50% of frequencies)
    high_freq_idx = int(len(freqs) * 0.5)
    high_freq_psd = psd[high_freq_idx:]
    
    if len(high_freq_psd) == 0 or np.mean(high_freq_psd) == 0:
        raise ValueError("High-frequency band empty or zero")
    
    max_low_peak = np.max(low_freq_psd)
    mean_high_floor = np.mean(high_freq_psd)
    
    return max_low_peak / mean_high_floor

def interpolate_missing_values(series: pd.Series) -> pd.Series:
    """Alias for interpolate_missing for compatibility."""
    return interpolate_missing(series)

def main():
    """CLI entry point for preprocessing."""
    import argparse
    import json
    from pathlib import Path
    
    parser = argparse.ArgumentParser(description='Preprocess time series datasets')
    parser.add_argument('--input', type=str, required=True, help='Input dataset manifest')
    parser.add_argument('--output', type=str, required=True, help='Output processed data')
    parser.add_argument('--max-lag', type=int, default=20, help='Maximum lag for ACF')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    # Load manifest
    with open(input_path, 'r') as f:
        manifest = json.load(f)
    
    # Process datasets
    results = preprocess_dataset(manifest, max_lag=args.max_lag)
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    log_info(f"Preprocessing complete. Processed: {len(results['processed'])}, Skipped: {len(results['skipped'])}")
    
    return results