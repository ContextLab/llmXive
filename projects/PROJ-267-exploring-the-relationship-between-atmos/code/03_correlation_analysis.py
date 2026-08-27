import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.ar_model import AutoReg
from statsmodels.stats.stattools import neweywest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_merged_data(file_path: str) -> pd.DataFrame:
    """Load the merged monthly dataset."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Merged data file not found: {file_path}")
    
    logger.info(f"Loading merged data from {file_path}")
    df = pd.read_csv(path)
    
    # Ensure date is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    
    # Validate required columns
    required_cols = ['date', 'ar_intensity', 'gravity_anomaly', 'uncertainty']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Drop rows with NaN in key columns
    initial_count = len(df)
    df = df.dropna(subset=required_cols)
    dropped = initial_count - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows with NaN values in key columns")
    
    return df

def calculate_effective_sample_size(n: int, rho: float) -> float:
    """
    Calculate effective sample size for autocorrelated time series.
    Uses the approximation n_eff = n * (1 - rho) / (1 + rho)
    where rho is the lag-1 autocorrelation.
    """
    if abs(rho) >= 1.0:
        # Prevent division by zero or negative effective size
        return 1.0
    return n * (1 - rho) / (1 + rho)

def prewhiten_series(series: pd.Series) -> Tuple[pd.Series, float]:
    """
    Pre-whiten a time series using AR(1) model.
    Returns residuals and the estimated lag-1 autocorrelation.
    """
    # Remove NaNs for fitting
    clean_series = series.dropna()
    if len(clean_series) < 10:
        logger.warning("Series too short for AR(1) pre-whitening, returning original")
        return series, 0.0

    try:
        model = AutoReg(clean_series, lags=1, old_names=False)
        result = model.fit()
        resid = result.resid
        # The AR(1) coefficient is the lag-1 autocorrelation estimate
        rho = result.params[1] if len(result.params) > 1 else 0.0
        return resid, rho
    except Exception as e:
        logger.warning(f"AR(1) pre-whitening failed: {e}. Returning original series.")
        return clean_series, 0.0

def compute_pearson_with_correction(x: pd.Series, y: pd.Series) -> Tuple[float, float, int]:
    """
    Compute Pearson correlation with autocorrelation correction.
    Returns (correlation, p_value, effective_n).
    """
    # Pre-whiten both series
    x_resid, rho_x = prewhiten_series(x)
    y_resid, rho_y = prewhiten_series(y)
    
    # Align lengths
    min_len = min(len(x_resid), len(y_resid))
    if min_len < 3:
        raise ValueError("Insufficient data points after pre-whitening")
    
    x_adj = x_resid.iloc[:min_len]
    y_adj = y_resid.iloc[:min_len]
    
    # Compute raw correlation
    r, p_raw = pearsonr(x_adj, y_adj)
    
    # Calculate effective sample size based on average autocorrelation
    rho_avg = (abs(rho_x) + abs(rho_y)) / 2
    eff_n = calculate_effective_sample_size(min_len, rho_avg)
    
    return r, p_raw, int(eff_n)

def bootstrap_confidence_interval(x: pd.Series, y: pd.Series, iterations: int = 1000, seed: int = 42) -> Tuple[float, float]:
    """
    Compute 95% bootstrap confidence interval for Pearson correlation.
    """
    np.random.seed(seed)
    n = len(x)
    boot_r = []
    
    for _ in range(iterations):
        idx = np.random.choice(n, n, replace=True)
        x_boot = x.iloc[idx]
        y_boot = y.iloc[idx]
        r, _ = pearsonr(x_boot, y_boot)
        boot_r.append(r)
    
    ci_low = np.percentile(boot_r, 2.5)
    ci_high = np.percentile(boot_r, 97.5)
    return ci_low, ci_high

def newey_west_standard_error(x: pd.Series, y: pd.Series, lags: int = 1) -> float:
    """
    Calculate Newey-West standard error for correlation coefficient.
    Uses statsmodels implementation.
    """
    # Create a dummy regression to use NeweyWest covariance
    # We correlate y with x, so we treat y as dependent and x as independent
    # Note: This is a simplified approach; full Newey-West for correlation
    # requires specific implementation, but we use the robust covariance
    # from regression as a proxy for the standard error of the slope,
    # which relates to the correlation.
    
    try:
        from statsmodels.regression.linear_model import OLS
        from statsmodels.stats.sandwich_covariance import cov_hac_simple
        
        # Add constant for intercept
        X = sm.add_constant(x.values)
        y_vals = y.values
        
        model = OLS(y_vals, X)
        results = model.fit()
        
        # HAC covariance
        cov_matrix = cov_hac_simple(results, max_lags=lags)
        # SE for the slope coefficient (index 1)
        se = np.sqrt(cov_matrix[1, 1])
        
        return se
    except ImportError:
        logger.warning("statsmodels.stats.sandwich_covariance not available, using fallback")
        # Fallback: simple standard error estimate
        n = len(x)
        if n < 2:
            return 1.0
        # Approximate SE for correlation: sqrt((1-r^2)/(n-2))
        r, _ = pearsonr(x, y)
        return np.sqrt((1 - r**2) / (n - 2)) if n > 2 else 1.0

def analyze_correlation_with_lags(df: pd.DataFrame, max_lag: int = 6) -> List[Dict[str, Any]]:
    """
    Analyze correlations across multiple lags.
    For each lag k, correlate AR(t) with Gravity(t-k).
    """
    results = []
    dates = df['date'].values
    ar = df['ar_intensity'].values
    grav = df['gravity_anomaly'].values
    unc = df['uncertainty'].values
    
    for lag in range(max_lag + 1):
        if lag == 0:
            x = ar
            y = grav
        else:
            # Shift gravity back by lag months
            x = ar[lag:]
            y = grav[:-lag]
            unc_shifted = unc[:-lag]
        
        if len(x) < 10:
            logger.warning(f"Not enough data for lag {lag}, skipping")
            continue
        
        try:
            r, p_raw, eff_n = compute_pearson_with_correction(pd.Series(x), pd.Series(y))
            ci_low, ci_high = bootstrap_confidence_interval(pd.Series(x), pd.Series(y))
            
            # Calculate SNR: r / uncertainty (using mean uncertainty of the aligned segment)
            if lag > 0:
                mean_unc = np.mean(unc_shifted)
            else:
                mean_unc = np.mean(unc)
            
            snr = r / mean_unc if mean_unc != 0 else 0.0
            
            results.append({
                'lag': lag,
                'correlation_coefficient': r,
                'raw_p_value': p_raw,
                'corrected_p_value': np.nan, # To be filled later
                'confidence_interval_lower': ci_low,
                'confidence_interval_upper': ci_high,
                'region_type': 'target',
                'signal_to_noise_ratio': snr,
                'effective_n': eff_n
            })
        except Exception as e:
            logger.error(f"Error computing correlation for lag {lag}: {e}")
            continue
    
    return results

def apply_fdr_correction(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Apply False Discovery Rate (FDR) correction to p-values.
    """
    if not results:
        return results
    
    p_values = [r['raw_p_value'] for r in results]
    # Filter out NaNs for correction
    valid_indices = [i for i, p in enumerate(p_values) if not np.isnan(p)]
    
    if len(valid_indices) == 0:
        return results
    
    valid_p = [p_values[i] for i in valid_indices]
    reject, p_corrected, _, _ = multipletests(valid_p, method='fdr_bh')
    
    for i, idx in enumerate(valid_indices):
        results[idx]['corrected_p_value'] = p_corrected[i]
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: str):
    """Save correlation results to CSV."""
    df = pd.DataFrame(results)
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved correlation results to {output_path}")

def main():
    """Main entry point for correlation analysis."""
    # Paths
    merged_path = 'data/processed/merged_monthly.csv'
    output_path = 'data/processed/correlation_results.csv'
    
    # Load data
    df = load_merged_data(merged_path)
    logger.info(f"Loaded {len(df)} records")
    
    # Analyze correlations with lags
    results = analyze_correlation_with_lags(df, max_lag=6)
    
    if not results:
        logger.error("No correlation results generated.")
        sys.exit(1)
    
    # Apply FDR correction
    results = apply_fdr_correction(results)
    
    # Save results
    save_results(results, output_path)
    
    # Print summary
    logger.info("Correlation Analysis Summary:")
    for r in results:
        logger.info(f"Lag {r['lag']}: r={r['correlation_coefficient']:.3f}, "
                   f"p_raw={r['raw_p_value']:.4f}, "
                   f"p_corr={r['corrected_p_value']:.4f}, "
                   f"SNR={r['signal_to_noise_ratio']:.3f}")

if __name__ == "__main__":
    main()
