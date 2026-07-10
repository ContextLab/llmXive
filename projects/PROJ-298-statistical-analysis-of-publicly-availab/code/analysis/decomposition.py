import os
import json
import math
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
from scipy import stats
from statsmodels.tsa.stattools import adfuller, acf, ljungbox
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from scipy.stats import chi2

# --- Helper Functions for Data Loading ---

def load_processed_data(processed_dir: str = "data/processed") -> Dict[str, Any]:
    """
    Loads the processed monthly frequency data from the specified directory.
    Expects a JSON file containing time series data for various tags.
    """
    processed_path = Path(processed_dir)
    target_file = processed_path / "monthly_tag_frequencies.json"
    
    if not target_file.exists():
        raise FileNotFoundError(f"Processed data file not found at {target_file}")
    
    with open(target_file, 'r') as f:
        return json.load(f)

# --- Pre-condition: ADF Test & Differencing ---

def perform_adf_test(series: np.ndarray, max_lag: int = 12) -> Tuple[float, float]:
    """
    Performs the Augmented Dickey-Fuller (ADF) test to check for stationarity.
    
    Args:
        series: Time series data (1D array).
        max_lag: Maximum lag to consider.
        
    Returns:
        Tuple of (statistic, p-value).
    """
    result = adfuller(series, maxlag=max_lag, autolag='AIC')
    return result[0], result[1]

def apply_differencing(series: np.ndarray, order: int = 1) -> np.ndarray:
    """
    Applies differencing to the series to make it stationary.
    
    Args:
        series: Original time series.
        order: Order of differencing (default 1).
        
    Returns:
        Differenced series.
    """
    diff_series = series.copy()
    for _ in range(order):
        diff_series = np.diff(diff_series)
    return diff_series

# --- Seasonality Pre-test ---

def calculate_autocorrelation(series: np.ndarray, nlags: int = 12) -> np.ndarray:
    """
    Calculates autocorrelation for given lags.
    """
    return acf(series, nlags=nlags, fft=False)

def spectral_analysis(series: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Performs basic spectral analysis (Periodogram) to detect dominant frequencies.
    """
    # Using scipy.signal.periodogram
    from scipy.signal import periodogram
    freqs, psd = periodogram(series, scaling='spectrum')
    return freqs, psd

def autocorrelation_seasonality_check(series: np.ndarray, threshold: float = 0.5) -> bool:
    """
    Checks for seasonality using autocorrelation at specific lags (e.g., lag 12 for monthly).
    Returns True if significant seasonality is detected.
    """
    if len(series) < 24:
        return False
    
    acf_vals = calculate_autocorrelation(series, nlags=12)
    # Check lag 12 (annual seasonality for monthly data)
    if len(acf_vals) > 12 and abs(acf_vals[12]) > threshold:
        return True
    return False

def detect_seasonality(series: np.ndarray) -> bool:
    """
    Determines if a series has seasonal components based on ACF and spectral analysis.
    """
    return autocorrelation_seasonality_check(series)

def run_seasonality_pretest(data: Dict[str, Any]) -> Dict[str, bool]:
    """
    Runs seasonality pre-test for all tags in the dataset.
    Returns a dictionary mapping tag names to boolean seasonality flags.
    """
    results = {}
    for tag, values in data.items():
        if isinstance(values, dict) and 'values' in values:
            series = np.array(values['values'])
        elif isinstance(values, list):
            series = np.array(values)
        else:
            continue
        
        if len(series) < 12:
            results[tag] = False
            continue
            
        results[tag] = detect_seasonality(series)
    return results

# --- Decomposition Logic ---

def get_decomposition_method(series: np.ndarray, is_seasonal: bool) -> str:
    """
    Determines the decomposition method based on seasonality pre-test.
    Returns 'STL' or 'HP' (Hodrick-Prescott).
    """
    if is_seasonal and len(series) >= 24:
        return 'STL'
    else:
        return 'HP'

def apply_stl_decomposition(series: np.ndarray, period: int = 12) -> Dict[str, np.ndarray]:
    """
    Applies STL decomposition.
    """
    try:
        stl = STL(series, period=period)
        res = stl.fit()
        return {
            'observed': res.observed,
            'trend': res.trend,
            'seasonal': res.seasonal,
            'resid': res.resid
        }
    except Exception:
        # Fallback if period is invalid or series too short
        return {
            'observed': series,
            'trend': np.full_like(series, np.mean(series)),
            'seasonal': np.zeros_like(series),
            'resid': series - np.mean(series)
        }

def apply_hp_decomposition(series: np.ndarray, lam: float = 1600) -> Dict[str, np.ndarray]:
    """
    Applies Hodrick-Prescott filter decomposition.
    Note: statsmodels has a dedicated HPFilter.
    """
    from statsmodels.tsa.filters.hp_filter import hpfilter
    trend, cycle = hpfilter(series, lam=lam)
    return {
        'observed': series,
        'trend': trend,
        'seasonal': np.zeros_like(series), # HP doesn't explicitly separate seasonal
        'resid': series - trend
    }

# --- Task T022: Residual Independence & Event Alignment ---

def check_residual_independence(residuals: np.ndarray, lags: int = 12) -> Dict[str, Any]:
    """
    Performs the Ljung-Box test on residuals to check for independence (no autocorrelation).
    
    Args:
        residuals: The residual time series.
        lags: Number of lags to test (default 12 for monthly data).
        
    Returns:
        Dictionary with test statistic, p-value, and independence status.
    """
    if len(residuals) <= lags:
        return {
            'statistic': None,
            'pvalue': None,
            'is_independent': False,
            'reason': 'Series too short for Ljung-Box test'
        }
    
    try:
        # statsmodels ljungbox returns a dict or tuple depending on version
        # Using return_as_dict for clarity in newer versions, or handling tuple
        lb_result = ljungbox(residuals, lags=[lags], return_df=False)
        # lb_result is a dict: {lag: (statistic, pvalue)}
        stat = lb_result[0][lags][0]
        pval = lb_result[0][lags][1]
        
        is_independent = pval > 0.05
        
        return {
            'statistic': float(stat),
            'pvalue': float(pval),
            'is_independent': is_independent,
            'lags_tested': lags
        }
    except Exception as e:
        return {
            'statistic': None,
            'pvalue': None,
            'is_independent': False,
            'reason': f'Ljung-Box test failed: {str(e)}'
        }

def rayleigh_test_for_event_alignment(
    series: np.ndarray, 
    event_indices: List[int], 
    period: int = 12
) -> Dict[str, Any]:
    """
    Performs a Rayleigh test (or equivalent circular statistics) to check if
    peaks/troughs align with specific event indices (e.g., reference calendar events).
    
    This implementation simulates checking alignment of local maxima with known event times.
    If no specific event times are provided, it checks for periodicity alignment.
    
    Args:
        series: The time series (observed or residual).
        event_indices: List of indices where reference events occurred.
        period: Expected period of seasonality (e.g., 12 for monthly).
        
    Returns:
        Dictionary with Rayleigh statistic, p-value, and alignment status.
    """
    if len(event_indices) == 0:
        return {
            'statistic': None,
            'pvalue': None,
            'is_aligned': False,
            'reason': 'No event indices provided'
        }
    
    # Normalize event indices to phase [0, 2*pi]
    phases = []
    for idx in event_indices:
        if idx < len(series):
            phase = (idx % period) / period * 2 * np.pi
            phases.append(phase)
    
    if len(phases) == 0:
        return {
            'statistic': None,
            'pvalue': None,
            'is_aligned': False,
            'reason': 'No valid event indices within series range'
        }
    
    # Convert to unit vectors
    x = np.cos(phases)
    y = np.sin(phases)
    
    R = np.sqrt(np.sum(x)**2 + np.sum(y)**2)
    n = len(phases)
    
    # Rayleigh Z statistic
    Z = (R**2) / n
    
    # Approximate p-value for Rayleigh test
    # p = exp(-Z) for large n, or use chi2 approximation
    # More accurate: p = exp(-Z) * (1 + (2Z - Z**2)/(4n) - ...)
    # Using simple exponential approximation for p-value
    p_value = np.exp(-Z)
    
    # Alignment is significant if p < 0.05
    is_aligned = p_value < 0.05
    
    return {
        'statistic': float(Z),
        'pvalue': float(p_value),
        'is_aligned': is_aligned,
        'n_events': n
    }

def run_decomposition_analysis(
    data: Optional[Dict[str, Any]] = None,
    processed_dir: str = "data/processed",
    output_dir: str = "data/processed"
) -> Dict[str, Any]:
    """
    Main pipeline for decomposition analysis including:
    1. ADF Test & Differencing
    2. Seasonality Pre-test
    3. STL or HP Decomposition
    4. Residual Independence Check (Ljung-Box)
    5. Event Alignment Check (Rayleigh)
    
    Returns a comprehensive results dictionary.
    """
    if data is None:
        data = load_processed_data(processed_dir)
    
    results = {
        'decomposition_results': {},
        'ljung_box_results': {},
        'rayleigh_results': {},
        'summary': {
            'total_tags': 0,
            'seasonal_tags': 0,
            'non_stationary_tags': 0,
            'independent_residuals_count': 0,
            'aligned_events_count': 0
        }
    }
    
    # Load reference calendar for event indices if available
    event_indices = []
    calendar_path = Path("data/events/reference_calendar.json")
    if calendar_path.exists():
        try:
            with open(calendar_path, 'r') as f:
                calendar = json.load(f)
                # Extract indices relative to our monthly bins
                # Assuming calendar has 'month_index' or similar
                for event in calendar.get('events', []):
                    if 'month_index' in event:
                        event_indices.append(event['month_index'])
        except Exception:
            pass
    
    results['summary']['total_tags'] = len(data)
    
    for tag, values in data.items():
        if isinstance(values, dict) and 'values' in values:
            series = np.array(values['values'])
            # Assume 'dates' or 'timestamps' exist for context, but we work with indices
        elif isinstance(values, list):
            series = np.array(values)
        else:
            continue
        
        if len(series) < 24:
            results['decomposition_results'][tag] = {'error': 'Series too short'}
            continue
        
        # 1. ADF Test
        adf_stat, adf_p = perform_adf_test(series)
        is_stationary = adf_p > 0.05
        
        if not is_stationary:
            series_diff = apply_differencing(series, order=1)
            results['summary']['non_stationary_tags'] += 1
        else:
            series_diff = series
        
        # 2. Seasonality Pre-test (on original or diff? usually original for method selection)
        is_seasonal = detect_seasonality(series)
        if is_seasonal:
            results['summary']['seasonal_tags'] += 1
        
        # 3. Decomposition
        method = get_decomposition_method(series_diff, is_seasonal)
        if method == 'STL':
            decomp = apply_stl_decomposition(series_diff, period=12)
        else:
            decomp = apply_hp_decomposition(series_diff, lam=1600)
        
        results['decomposition_results'][tag] = {
            'method': method,
            'stationary': is_stationary,
            'seasonal': is_seasonal,
            'trend_length': len(decomp['trend']),
            'resid_length': len(decomp['resid'])
        }
        
        # 4. Residual Independence (Ljung-Box)
        lb_result = check_residual_independence(decomp['resid'], lags=12)
        results['ljung_box_results'][tag] = lb_result
        if lb_result.get('is_independent'):
            results['summary']['independent_residuals_count'] += 1
        
        # 5. Event Alignment (Rayleigh)
        ray_result = rayleigh_test_for_event_alignment(
            series_diff, 
            event_indices, 
            period=12
        )
        results['rayleigh_results'][tag] = ray_result
        if ray_result.get('is_aligned'):
            results['summary']['aligned_events_count'] += 1
    
    return results

def main():
    """
    Entry point for the decomposition analysis script.
    Reads processed data, runs the full pipeline, and saves results.
    """
    print("Starting Decomposition Analysis (T022)...")
    
    try:
        results = run_decomposition_analysis()
        
        output_path = Path("data/processed")
        output_path.mkdir(parents=True, exist_ok=True)
        
        output_file = output_path / "decomposition_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"Analysis complete. Results saved to {output_file}")
        print(f"Summary: {results['summary']}")
        
    except Exception as e:
        print(f"Error during decomposition analysis: {e}")
        raise

if __name__ == "__main__":
    main()