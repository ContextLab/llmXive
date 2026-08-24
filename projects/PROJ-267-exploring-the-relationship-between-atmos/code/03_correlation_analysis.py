"""
Correlation and Bootstrap Analysis Script (T020)

Computes Pearson correlation between AR intensity and gravity anomalies across lag windows.
Implements AR(1) pre-whitening, bootstrap resampling, FDR correction, and Newey-West SEs.
Outputs: data/processed/correlation_results.csv
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from scipy.stats import pearsonr, t
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.stattools import acf
from statsmodels.regression.linear_model import OLS
from statsmodels.stats.sandwich_covariance import cov_hac

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
BOOTSTRAP_ITERATIONS = 1000
BOOTSTRAP_SEED = 42
LAG_WINDOW = range(-3, 4)  # -3 to +3 months
ALPHA = 0.05
FDR_METHOD = 'fdr_bh'  # Benjamini-Hochberg

def load_merged_data(input_path: str) -> pd.DataFrame:
    """Load the merged monthly dataset."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Merged data not found at {input_path}. Run preprocessing first.")
    df = pd.read_csv(input_path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    return df

def calculate_effective_sample_size(n: int, rho: float) -> float:
    """
    Calculate effective sample size (ESS) for time series with autocorrelation.
    n: original sample size
    rho: lag-1 autocorrelation coefficient
    """
    if abs(rho) >= 1.0:
        return 1.0  # Degenerate case
    # Approximation for ESS with AR(1)
    ess = n * (1.0 - rho) / (1.0 + rho)
    return max(1.0, ess)

def prewhiten_series(series: pd.Series) -> Tuple[pd.Series, float]:
    """
    Pre-whiten a series using AR(1) model to remove autocorrelation.
    Returns the residuals and the estimated lag-1 autocorrelation.
    """
    # Estimate lag-1 autocorrelation
    acf_vals = acf(series, nlags=1, fft=False)
    rho = acf_vals[1] if len(acf_vals) > 1 else 0.0

    # Apply AR(1) filter: y_t - rho * y_{t-1}
    # Drop first element to align
    prewhitened = series.diff().dropna()
    # Adjust for the mean shift introduced by differencing if necessary,
    # but for correlation of residuals, simple differencing is a common first-order pre-whitening.
    # A more rigorous approach: fit AR(1), get residuals.
    # Let's fit AR(1) explicitly to get true residuals.
    try:
        # Simple AR(1) fit: y_t = c + phi * y_{t-1} + e_t
        lagged = series.shift(1).dropna()
        current = series.iloc[1:].dropna()
        if len(lagged) < 10:
            return series, 0.0 # Not enough data
        
        X = lagged.values.reshape(-1, 1)
        y = current.values
        model = OLS(y, X).fit()
        residuals = model.resid
        return pd.Series(residuals, index=current.index), model.params[0]
    except Exception as e:
        logger.warning(f"AR(1) fit failed: {e}. Using raw series.")
        return series, 0.0

def compute_pearson_with_correction(x: pd.Series, y: pd.Series) -> Dict[str, float]:
    """
    Compute Pearson correlation with autocorrelation correction via effective sample size.
    Returns correlation, p-value (adjusted for ESS), and ESS.
    """
    # Pre-whiten both series
    x_res, rho_x = prewhiten_series(x)
    y_res, rho_y = prewhiten_series(y)
    
    # Align indices after pre-whitening
    common_idx = x_res.index.intersection(y_res.index)
    if len(common_idx) < 10:
        return {'r': 0.0, 'p_value': 1.0, 'ess': 0.0}

    x_clean = x_res.loc[common_idx]
    y_clean = y_res.loc[common_idx]

    # Compute Pearson on residuals
    r, p_raw = pearsonr(x_clean, y_clean)

    # Calculate ESS based on average rho or individual?
    # Using average rho for simplicity in ESS approximation
    avg_rho = (rho_x + rho_y) / 2.0
    n = len(common_idx)
    ess = calculate_effective_sample_size(n, avg_rho)

    # Adjust p-value using t-distribution with ESS degrees of freedom
    # t = r * sqrt((n-2) / (1-r^2)) -> use ess instead of n
    if abs(r) >= 1.0:
        p_adj = 0.0
    else:
        t_stat = r * np.sqrt((ess - 2) / (1 - r**2))
        p_adj = 2 * (1 - t.cdf(abs(t_stat), df=ess - 2))

    return {
        'r': r,
        'p_value': p_adj,
        'ess': ess,
        'rho_x': rho_x,
        'rho_y': rho_y
    }

def bootstrap_confidence_interval(x: pd.Series, y: pd.Series, iterations: int = 1000, seed: int = 42) -> Tuple[float, float]:
    """
    Compute 95% confidence interval for Pearson r using bootstrap resampling.
    """
    np.random.seed(seed)
    n = len(x)
    bootstrap_rs = []

    for _ in range(iterations):
        idx = np.random.choice(n, size=n, replace=True)
        x_boot = x.iloc[idx]
        y_boot = y.iloc[idx]
        r, _ = pearsonr(x_boot, y_boot)
        bootstrap_rs.append(r)

    return float(np.percentile(bootstrap_rs, 2.5)), float(np.percentile(bootstrap_rs, 97.5))

def newey_west_standard_error(x: pd.Series, y: pd.Series, max_lags: int = 4) -> float:
    """
    Calculate Newey-West (HAC) standard error for the correlation coefficient.
    We treat the correlation estimation as a regression problem for robust SE.
    """
    # Simple linear regression y ~ x to get residuals and SE, then apply HAC
    # This is a proxy for the SE of the correlation coefficient
    try:
        X = x.values.reshape(-1, 1)
        y = y.values
        model = OLS(y, X).fit()
        # HAC covariance matrix
        cov_matrix = cov_hac(model, maxlags=max_lags)
        se = np.sqrt(cov_matrix[1, 1]) # SE of slope
        # Convert slope SE to correlation SE approximation? 
        # For the purpose of this task, we return the HAC SE of the slope as a robust metric.
        # A more direct SE for r is complex; using slope SE as a proxy for robustness check.
        return float(se)
    except Exception as e:
        logger.warning(f"Newey-West calculation failed: {e}")
        return 0.0

def analyze_correlation_with_lags(df: pd.DataFrame, lag: int, target_col: str = 'ar_intensity', 
                                  gravity_col: str = 'gravity_anomaly', 
                                  uncertainty_col: str = 'uncertainty') -> Dict[str, Any]:
    """
    Analyze correlation at a specific lag.
    Positive lag: AR leads Gravity (AR_t vs Gravity_{t+lag})
    Negative lag: Gravity leads AR (AR_t vs Gravity_{t+lag} where lag is negative)
    """
    if lag == 0:
        x = df[target_col]
        y = df[gravity_col]
    elif lag > 0:
        # AR_t vs Gravity_{t+lag} -> shift gravity back
        x = df[target_col].iloc[:-lag]
        y = df[gravity_col].iloc[lag:]
    else:
        # AR_t vs Gravity_{t+lag} (lag is negative) -> shift AR back
        # e.g. lag = -1: AR_{t+1} vs Gravity_t -> shift AR forward
        shift = abs(lag)
        x = df[target_col].iloc[shift:]
        y = df[gravity_col].iloc[:-shift]

    if len(x) < 10:
        return None

    # Compute metrics
    stats = compute_pearson_with_correction(x, y)
    ci_lower, ci_upper = bootstrap_confidence_interval(x, y, BOOTSTRAP_ITERATIONS, BOOTSTRAP_SEED)
    se = newey_west_standard_error(x, y)
    
    # Signal to Noise Ratio: r / uncertainty (using mean uncertainty of the overlapping period)
    # We need to align uncertainty values too.
    if lag == 0:
        u = df[uncertainty_col]
    elif lag > 0:
        u = df[uncertainty_col].iloc[lag:]
    else:
        u = df[uncertainty_col].iloc[:lag] # lag is negative, so :lag works (e.g. :-1)
    
    mean_uncertainty = u.mean()
    if mean_uncertainty > 0:
        snr = stats['r'] / mean_uncertainty
    else:
        snr = 0.0

    return {
        'lag': lag,
        'correlation_coefficient': stats['r'],
        'raw_p_value': stats['p_value'],
        'confidence_interval_lower': ci_lower,
        'confidence_interval_upper': ci_upper,
        'signal_to_noise_ratio': snr,
        'effective_sample_size': stats['ess'],
        'newey_west_se': se,
        'n_observations': len(x)
    }

def apply_fdr_correction(results: List[Dict], alpha: float = ALPHA, method: str = FDR_METHOD) -> List[Dict]:
    """
    Apply False Discovery Rate correction to p-values.
    """
    p_values = [r['raw_p_value'] for r in results]
    if not p_values:
        return results

    reject, p_corrected, _, _ = multipletests(p_values, alpha=alpha, method=method)
    
    for i, r in enumerate(results):
        r['corrected_p_value'] = p_corrected[i]
        r['significance_flag'] = bool(reject[i])
    
    return results

def save_results(results: List[Dict], output_path: str, region_type: str = 'target'):
    """
    Save results to CSV.
    """
    df = pd.DataFrame(results)
    df['region_type'] = region_type
    df = df[['lag', 'correlation_coefficient', 'raw_p_value', 'corrected_p_value', 
             'confidence_interval_lower', 'confidence_interval_upper', 
             'significance_flag', 'region_type', 'signal_to_noise_ratio',
             'effective_sample_size', 'newey_west_se', 'n_observations']]
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")

def main():
    input_path = 'data/processed/merged_monthly.csv'
    output_path = 'data/processed/correlation_results.csv'
    
    logger.info(f"Loading data from {input_path}")
    df = load_merged_data(input_path)
    
    logger.info(f"Analyzing correlations for lags: {list(LAG_WINDOW)}")
    results = []
    for lag in LAG_WINDOW:
        res = analyze_correlation_with_lags(df, lag)
        if res:
            results.append(res)
    
    if not results:
        logger.error("No valid correlation results computed.")
        sys.exit(1)

    logger.info("Applying FDR correction...")
    results = apply_fdr_correction(results)
    
    logger.info(f"Saving results to {output_path}")
    save_results(results, output_path, region_type='target')
    
    # Log summary
    significant = sum(1 for r in results if r['significance_flag'])
    logger.info(f"Analysis complete. {significant}/{len(results)} lags significant (FDR corrected).")

if __name__ == '__main__':
    main()