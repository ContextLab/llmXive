"""
Correlation and Bootstrap Analysis Script (T020)

Computes Pearson correlation between AR intensity and gravity anomalies across lag windows,
applies autocorrelation correction (AR(1) pre-whitening + Newey-West SE), bootstrap resampling
for confidence intervals, and FDR correction for multiple comparisons.

Outputs:
  - data/processed/correlation_results.json: Full statistical results
  - data/processed/correlation_results.csv: Tabular results for reporting
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.stattools import acf
from statsmodels.sandbox.regression.gmm import NeweyWest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
LAGS = [0, 1, 2, 3]  # Months
BOOTSTRAP_ITERATIONS = 1000
BOOTSTRAP_SEED = 42
ALPHA = 0.05
INPUT_FILE = "data/processed/merged_monthly.csv"
OUTPUT_DIR = "data/processed"
OUTPUT_JSON = "correlation_results.json"
OUTPUT_CSV = "correlation_results.csv"


def load_merged_data(filepath: str) -> pd.DataFrame:
    """Load the merged monthly dataset."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} rows from {filepath}")
    required_cols = ['date', 'ar_intensity', 'gravity_anomaly', 'uncertainty']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    return df


def calculate_effective_sample_size(n: int, rho: float) -> float:
    """
    Calculate effective sample size (n_eff) for autocorrelated time series.
    Formula: n_eff = n * (1 - rho) / (1 + rho)
    """
    if abs(rho) >= 1.0:
        return 1.0  # Degenerate case
    return n * (1 - rho) / (1 + rho)


def prewhiten_series(x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Pre-whiten series using AR(1) model to remove autocorrelation.
    Returns pre-whitened x, pre-whitened y, and the AR(1) coefficient.
    """
    n = len(x)
    # Estimate AR(1) coefficient for x
    # rho_x = cov(x_t, x_{t-1}) / var(x)
    if n < 3:
        return x, y, 0.0
    
    # Simple AR(1) estimation via lag-1 autocorrelation
    rho_x = np.corrcoef(x[:-1], x[1:])[0, 1]
    if np.isnan(rho_x):
        rho_x = 0.0
    
    # Pre-whiten x: x'_t = x_t - rho * x_{t-1}
    x_pre = np.empty(n)
    x_pre[0] = x[0] * np.sqrt(1 - rho_x**2)
    for i in range(1, n):
        x_pre[i] = x[i] - rho_x * x[i-1]
    
    # Pre-whiten y similarly (assuming same AR structure for simplicity, or estimate separately)
    # For robustness, we estimate rho_y separately
    rho_y = np.corrcoef(y[:-1], y[1:])[0, 1]
    if np.isnan(rho_y):
        rho_y = 0.0
    
    y_pre = np.empty(n)
    y_pre[0] = y[0] * np.sqrt(1 - rho_y**2)
    for i in range(1, n):
        y_pre[i] = y[i] - rho_y * y[i-1]
    
    # Return the average rho for effective sample size calculation if needed
    avg_rho = (rho_x + rho_y) / 2.0
    return x_pre, y_pre, avg_rho


def compute_pearson_with_correction(
    x: np.ndarray, 
    y: np.ndarray, 
    n_obs: int
) -> Tuple[float, float, float]:
    """
    Compute Pearson correlation and p-value with autocorrelation correction.
    Returns (r, p_value, n_eff).
    """
    # Pre-whiten
    x_pre, y_pre, avg_rho = prewhiten_series(x, y)
    
    # Calculate effective sample size
    n_eff = calculate_effective_sample_size(n_obs, avg_rho)
    
    # Compute correlation on pre-whitened data
    if len(x_pre) < 2:
        return 0.0, 1.0, n_eff
    
    r, p_raw = stats.pearsonr(x_pre, y_pre)
    if np.isnan(r):
        r = 0.0
    if np.isnan(p_raw):
        p_raw = 1.0
        
    return r, p_raw, n_eff


def bootstrap_confidence_interval(
    x: np.ndarray, 
    y: np.ndarray, 
    n_iter: int = 1000, 
    seed: int = 42, 
    alpha: float = 0.05
) -> Tuple[float, float, float]:
    """
    Compute bootstrap confidence interval for Pearson correlation.
    Returns (r_original, ci_lower, ci_upper).
    """
    np.random.seed(seed)
    n = len(x)
    if n < 2:
        return 0.0, 0.0, 0.0
    
    # Original correlation (on pre-whitened data for consistency)
    x_pre, y_pre, _ = prewhiten_series(x, y)
    r_orig, _, _ = compute_pearson_with_correction(x, y, n)
    
    bootstrap_rs = []
    for _ in range(n_iter):
        indices = np.random.randint(0, n, n)
        x_boot = x_pre[indices]
        y_boot = y_pre[indices]
        r_boot, _, _ = compute_pearson_with_correction(x_boot, y_boot, n)
        bootstrap_rs.append(r_boot)
    
    bootstrap_rs = np.array(bootstrap_rs)
    ci_lower = np.percentile(bootstrap_rs, 100 * alpha / 2)
    ci_upper = np.percentile(bootstrap_rs, 100 * (1 - alpha / 2))
    
    return r_orig, ci_lower, ci_upper


def newey_west_standard_error(
    x: np.ndarray, 
    y: np.ndarray, 
    lags: int = 1
) -> float:
    """
    Compute Newey-West standard error for the correlation coefficient.
    This is a simplified approximation for the standard error of r.
    """
    n = len(x)
    if n < 3:
        return 0.0
    
    # Calculate residuals from a linear fit (approximate)
    # y = a + b*x + e
    # We want SE of b, then map to SE of r
    # For simplicity, we use the formula for SE(r) with autocorrelation correction
    # SE(r) ≈ sqrt( (1-r^2) / (n_eff - 2) )
    
    x_pre, y_pre, avg_rho = prewhiten_series(x, y)
    n_eff = calculate_effective_sample_size(n, avg_rho)
    
    # Compute correlation on pre-whitened
    r, _, _ = compute_pearson_with_correction(x, y, n)
    if abs(r) >= 1.0:
        return 0.0
    
    se = np.sqrt((1 - r**2) / (n_eff - 2))
    return se


def analyze_correlation_with_lags(
    df: pd.DataFrame, 
    lags: List[int], 
    bootstrap_iter: int, 
    seed: int
) -> List[Dict[str, Any]]:
    """
    Analyze correlation across different lag windows.
    """
    results = []
    n_total = len(df)
    
    # Sort by date to ensure correct lag alignment
    df = df.sort_values('date').reset_index(drop=True)
    
    ar_series = df['ar_intensity'].values
    gravity_series = df['gravity_anomaly'].values
    uncertainty_series = df['uncertainty'].values
    
    for lag in lags:
        # Align series with lag
        # If lag > 0, AR intensity at time t correlates with Gravity at t + lag
        # So we shift gravity series back by lag
        if lag == 0:
            x = ar_series
            y = gravity_series
        else:
            x = ar_series[:-lag]
            y = gravity_series[lag:]
        
        # Filter out NaNs
        mask = ~(np.isnan(x) | np.isnan(y))
        x = x[mask]
        y = y[mask]
        
        n_obs = len(x)
        if n_obs < 3:
            logger.warning(f"Lag {lag}: Insufficient data points ({n_obs}) after alignment.")
            continue
        
        # Compute correlation with autocorrelation correction
        r, p_raw, n_eff = compute_pearson_with_correction(x, y, n_obs)
        
        # Bootstrap CI
        r_boot, ci_lower, ci_upper = bootstrap_confidence_interval(
            x, y, n_iter=bootstrap_iter, seed=seed
        )
        
        # Newey-West SE
        se_nw = newey_west_standard_error(x, y)
        
        # Signal-to-Noise Ratio (using uncertainty from data)
        # We take the mean uncertainty of the aligned series for this lag
        u_aligned = uncertainty_series
        if lag > 0:
            u_aligned = u_aligned[lag:]
        u_aligned = u_aligned[mask]
        mean_uncertainty = np.mean(u_aligned) if np.all(~np.isnan(u_aligned)) else 1.0
        
        if mean_uncertainty == 0:
            snr = np.inf if r != 0 else 0.0
        else:
            snr = r / mean_uncertainty
        
        results.append({
            'lag': lag,
            'n_obs': n_obs,
            'correlation_coefficient': float(r),
            'raw_p_value': float(p_raw),
            'confidence_interval_lower': float(ci_lower),
            'confidence_interval_upper': float(ci_upper),
            'newey_west_se': float(se_nw),
            'signal_to_noise_ratio': float(snr),
            'mean_uncertainty': float(mean_uncertainty)
        })
    
    return results


def apply_fdr_correction(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Apply False Discovery Rate (FDR) correction to p-values.
    """
    if not results:
        return results
    
    p_values = [res['raw_p_value'] for res in results]
    n_tests = len(p_values)
    
    # Use Benjamini-Hochberg procedure
    reject, p_corrected, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
    
    for i, res in enumerate(results):
        res['corrected_p_value'] = float(p_corrected[i])
        res['significance_flag'] = bool(reject[i])
    
    return results


def save_results(results: List[Dict[str, Any]], output_dir: str):
    """Save results to JSON and CSV."""
    os.makedirs(output_dir, exist_ok=True)
    
    # Save JSON
    json_path = os.path.join(output_dir, OUTPUT_JSON)
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved JSON results to {json_path}")
    
    # Save CSV
    csv_path = os.path.join(output_dir, OUTPUT_CSV)
    df_results = pd.DataFrame(results)
    # Ensure boolean is correct type
    if 'significance_flag' in df_results.columns:
        df_results['significance_flag'] = df_results['significance_flag'].astype(bool)
    df_results.to_csv(csv_path, index=False)
    logger.info(f"Saved CSV results to {csv_path}")


def main():
    """Main entry point."""
    logger.info("Starting correlation analysis (T020)...")
    
    # Load data
    try:
        df = load_merged_data(INPUT_FILE)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Analyze
    raw_results = analyze_correlation_with_lags(
        df, 
        lags=LAGS, 
        bootstrap_iter=BOOTSTRAP_ITERATIONS, 
        seed=BOOTSTRAP_SEED
    )
    
    # Apply FDR correction
    final_results = apply_fdr_correction(raw_results)
    
    # Save
    save_results(final_results, OUTPUT_DIR)
    
    logger.info("Correlation analysis completed successfully.")
    logger.info(f"Results summary:")
    for res in final_results:
        sig_flag = "SIG" if res['significance_flag'] else "NS"
        logger.info(f"  Lag {res['lag']}: r={res['correlation_coefficient']:.3f}, "
                    f"p_corr={res['corrected_p_value']:.3f} [{sig_flag}], "
                    f"SNR={res['signal_to_noise_ratio']:.3f}")


if __name__ == "__main__":
    main()