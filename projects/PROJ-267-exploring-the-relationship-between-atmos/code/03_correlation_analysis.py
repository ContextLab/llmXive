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
import statsmodels.api as sm

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_merged_data(filepath: str) -> pd.DataFrame:
    """Load the merged dataset from CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Merged data file not found: {filepath}. Run T017c first.")
    df = pd.read_csv(filepath)
    df['date'] = pd.to_datetime(df['date'])
    return df

def calculate_effective_sample_size(n: int, rho: float) -> float:
    """
    Calculate effective sample size (n_eff) given autocorrelation (rho).
    Formula: n_eff = n * (1 - rho) / (1 + rho)
    """
    if abs(rho) >= 1.0:
        return 1.0 # Prevent division by zero or negative
    return n * (1 - rho) / (1 + rho)

def prewhiten_series(series: pd.Series) -> Tuple[np.ndarray, float]:
    """
    Fit AR(1) model and return residuals (pre-whitened series) and the AR(1) coefficient.
    """
    try:
        # Ensure no NaNs for fitting
        clean_series = series.dropna()
        if len(clean_series) < 5:
            logger.warning("Series too short for AR(1) pre-whitening. Returning original.")
            return clean_series.values, 0.0

        model = AutoReg(clean_series, lags=1, old_names=False)
        result = model.fit()
        resid = result.resid
        ar_coef = result.params[1] if len(result.params) > 1 else 0.0
        return resid, ar_coef
    except Exception as e:
        logger.warning(f"Pre-whitening failed: {e}. Returning original series.")
        return series.dropna().values, 0.0

def compute_pearson_with_correction(x: np.ndarray, y: np.ndarray) -> Tuple[float, float, float]:
    """
    Compute Pearson correlation, p-value, and effective sample size adjustment.
    Returns: (r, p_value, n_eff)
    """
    n = len(x)
    if n < 3:
        return 0.0, 1.0, n

    r, p_raw = pearsonr(x, y)

    # Estimate autocorrelation of residuals if we had a model, 
    # but for simple lag correction we often use the lag-1 autocorrelation of the series itself
    # as a proxy for the noise structure in time series correlation.
    # A more robust way is to prewhiten both, then correlate residuals.
    # Here we calculate rho_x and rho_y to adjust n_eff.
    
    # Simple lag-1 autocorrelation
    def lag1_autocorr(s):
        if len(s) < 3: return 0.0
        return np.corrcoef(s[:-1], s[1:])[0, 1]

    rho_x = lag1_autocorr(x) if len(x) > 2 else 0.0
    rho_y = lag1_autocorr(y) if len(y) > 2 else 0.0
    
    # Approximate effective rho for the pair
    rho_eff = (rho_x + rho_y) / 2.0
    
    n_eff = calculate_effective_sample_size(n, rho_eff)
    
    return r, p_raw, n_eff

def bootstrap_confidence_interval(x: np.ndarray, y: np.ndarray, iterations: int = 1000, seed: int = 42) -> Tuple[float, float]:
    """
    Compute 95% bootstrap confidence interval for Pearson r.
    """
    np.random.seed(seed)
    n = len(x)
    boot_r = []
    
    for _ in range(iterations):
        idx = np.random.choice(n, n, replace=True)
        # Ensure we have valid data points
        if len(idx) < 3:
            continue
        r, _ = pearsonr(x[idx], y[idx])
        boot_r.append(r)
    
    if len(boot_r) == 0:
        return 0.0, 0.0
    
    return np.percentile(boot_r, [2.5, 97.5])

def newey_west_standard_error(x: np.ndarray, y: np.ndarray, lags: int = 1) -> float:
    """
    Calculate Newey-West standard error for the slope in a simple regression y ~ x.
    This provides robust inference in the presence of autocorrelation and heteroskedasticity.
    """
    try:
        X = sm.add_constant(x)
        model = sm.OLS(y, X).fit()
        # HAC (Heteroskedasticity and Autocorrelation Consistent) covariance
        cov_matrix = model.get_robustcov_results(cov_type='HAC', maxlags=lags).cov_params()
        # Standard error of the slope (index 1)
        se = np.sqrt(cov_matrix.iloc[1, 1])
        return se
    except Exception as e:
        logger.warning(f"Newey-West SE calculation failed: {e}")
        return 0.0

def analyze_correlation_with_lags(df: pd.DataFrame, lags: List[int] = [-3, -2, -1, 0, 1, 2, 3]) -> List[Dict[str, Any]]:
    """
    Analyze correlations across multiple lags with pre-whitening and bootstrap.
    """
    results = []
    raw_p_values = []
    
    # Pre-whiten both series to remove autocorrelation structure
    ar_resid, _ = prewhiten_series(df['ar_intensity'])
    grav_resid, _ = prewhiten_series(df['gravity_anomaly'])
    
    # Handle NaNs resulting from pre-whitening or original data
    # We align the indices after shifting
    
    for lag in lags:
        x_shifted = ar_resid
        y_shifted = grav_resid
        
        # Shift logic:
        # If lag > 0: AR leads Gravity (AR[t] vs Grav[t+lag]) -> shift Grav back (drop first lag)
        # If lag < 0: AR lags Gravity (AR[t] vs Grav[t+lag]) -> shift AR back (drop first abs(lag))
        
        if lag > 0:
            x = ar_resid[:-lag]
            y = grav_resid[lag:]
        elif lag < 0:
            x = ar_resid[-lag:]
            y = grav_resid[:lag]
        else:
            x = ar_resid
            y = grav_resid

        if len(x) < 5:
            logger.warning(f"Lag {lag}: Insufficient data points ({len(x)}). Skipping.")
            continue

        # Compute correlation on pre-whitened residuals
        r, p_raw, n_eff = compute_pearson_with_correction(x, y)
        raw_p_values.append(p_raw)

        # Bootstrap CI on the aligned residuals
        ci_low, ci_high = bootstrap_confidence_interval(x, y)

        # Signal to Noise Ratio
        # Use the mean uncertainty from the original dataframe if available
        uncertainty = df['uncertainty'].mean() if 'uncertainty' in df.columns and not df['uncertainty'].isna().all() else 1.0
        snr = r / uncertainty if uncertainty != 0 else 0.0

        results.append({
            'lag': lag,
            'correlation_coefficient': float(r),
            'raw_p_value': float(p_raw),
            'confidence_interval_lower': float(ci_low),
            'confidence_interval_upper': float(ci_high),
            'region_type': 'target',
            'signal_to_noise_ratio': float(snr),
            'effective_n': int(n_eff)
        })

    # FDR Correction (Benjamini-Hochberg)
    if len(raw_p_values) > 0:
        _, p_corrected, _, _ = multipletests(raw_p_values, method='fdr_bh')
        for i, res in enumerate(results):
            res['corrected_p_value'] = float(p_corrected[i])
            res['significance_flag'] = bool(p_corrected[i] < 0.05)
    else:
        for res in results:
            res['corrected_p_value'] = 1.0
            res['significance_flag'] = False

    return results

def save_results(results: List[Dict[str, Any]], output_path: str):
    """Save results to CSV."""
    df = pd.DataFrame(results)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point for correlation analysis."""
    input_path = 'data/processed/merged_monthly.csv'
    output_path = 'data/processed/correlation_results.csv'
    
    logger.info("Starting correlation analysis...")
    
    try:
        df = load_merged_data(input_path)
        
        if df.empty:
            raise ValueError("Input dataframe is empty.")
        
        # Ensure required columns exist
        required_cols = ['ar_intensity', 'gravity_anomaly']
        if 'uncertainty' not in df.columns:
            logger.warning("Uncertainty column missing. Assuming unit uncertainty for SNR.")
            df['uncertainty'] = 1.0
        
        results = analyze_correlation_with_lags(df)
        
        if not results:
            raise ValueError("No correlation results generated. Check data alignment and length.")
        
        save_results(results, output_path)
        logger.info("Correlation analysis complete.")
        
    except Exception as e:
        logger.critical(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()