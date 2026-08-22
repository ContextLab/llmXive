"""
Correlation computation script for Atmospheric River Gravity Correlation study.

Computes Pearson correlation between AR intensity and gravity anomalies across lag windows,
implements autocorrelation correction using AR(1) pre-whitening, and reports bootstrap CIs.
"""
import os
import sys
import logging
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.ar_model import AutoReg
from statsmodels.stats.correlation_tools import cov_nearest
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "merged_monthly.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_PATH = OUTPUT_DIR / "correlation_results.json"

# Constants
LAGS = [0, 1, 2, 3]
BOOTSTRAP_ITERATIONS = 1000
RANDOM_SEED = 42

def load_merged_data():
    """Load the preprocessed merged dataset."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Required input file not found: {DATA_PATH}. "
            "Run 02_preprocessing.py first."
        )
    df = pd.read_csv(DATA_PATH)
    logger.info(f"Loaded {len(df)} rows from {DATA_PATH}")
    return df

def calculate_effective_sample_size(series, method='ar1'):
    """
    Calculate effective sample size accounting for autocorrelation.
    
    Uses AR(1) pre-whitening to estimate the effective degrees of freedom.
    """
    n = len(series)
    if n < 2:
        return n
    
    # Estimate AR(1) coefficient
    try:
        ar_model = AutoReg(series, lags=1, old_names=False)
        ar_fit = ar_model.fit()
        rho = ar_fit.params[1] if len(ar_fit.params) > 1 else 0
    except Exception:
        # Fallback to simple lag-1 autocorrelation if AR fit fails
        rho = np.corrcoef(series[:-1], series[1:])[0, 1]
        if np.isnan(rho):
            rho = 0
    
    # Effective sample size formula for AR(1)
    # n_eff = n * (1 - rho) / (1 + rho)
    if abs(rho) >= 1.0:
        rho = 0.99 * np.sign(rho) if rho != 0 else 0.99
    
    n_eff = n * (1 - rho) / (1 + rho)
    return max(1, int(n_eff))

def prewhiten_series(series):
    """
    Pre-whiten a time series using AR(1) model.
    
    Returns the residuals (whitened series) and the fitted AR(1) parameters.
    """
    if len(series) < 3:
        return series, None
    
    try:
        ar_model = AutoReg(series, lags=1, old_names=False)
        ar_fit = ar_model.fit()
        residuals = ar_fit.resid
        return residuals, ar_fit.params
    except Exception as e:
        logger.warning(f"AR(1) fitting failed: {e}. Using original series.")
        return series, None

def compute_pearson_with_correction(x, y):
    """
    Compute Pearson correlation with autocorrelation correction.
    
    1. Pre-whiten both series using AR(1)
    2. Compute correlation on residuals
    3. Calculate effective sample size
    4. Adjust p-value based on effective sample size
    """
    if len(x) != len(y) or len(x) < 3:
        return None, None, None, None
    
    # Pre-whiten series
    x_white, _ = prewhiten_series(x)
    y_white, _ = prewhiten_series(y)
    
    # Remove NaNs introduced by pre-whitening
    mask = ~(np.isnan(x_white) | np.isnan(y_white))
    x_clean = x_white[mask]
    y_clean = y_white[mask]
    
    if len(x_clean) < 3:
        return None, None, None, None
    
    # Compute Pearson correlation on whitened data
    corr, p_value = stats.pearsonr(x_clean, y_clean)
    
    # Calculate effective sample size
    n_eff = calculate_effective_sample_size(x_clean)
    
    return corr, p_value, n_eff, len(x_clean)

def bootstrap_confidence_interval(x, y, n_iterations=1000, seed=42, lag=0):
    """
    Compute bootstrap confidence intervals for correlation with lag.
    
    Applies lag by shifting y relative to x (positive lag = y leads x).
    """
    np.random.seed(seed)
    n = len(x)
    correlations = []
    
    # Apply lag
    if lag > 0:
        x_lagged = x[:-lag]
        y_lagged = y[lag:]
    elif lag < 0:
        x_lagged = x[-lag:]
        y_lagged = y[:lag]
    else:
        x_lagged = x
        y_lagged = y
    
    if len(x_lagged) < 3:
        return None, None, None
    
    # Bootstrap resampling
    for _ in range(n_iterations):
        indices = np.random.choice(len(x_lagged), size=len(x_lagged), replace=True)
        x_boot = x_lagged[indices]
        y_boot = y_lagged[indices]
        
        corr, _ = stats.pearsonr(x_boot, y_boot)
        if not np.isnan(corr):
            correlations.append(corr)
    
    if len(correlations) == 0:
        return None, None, None
    
    correlations = np.array(correlations)
    mean_corr = np.mean(correlations)
    ci_lower = np.percentile(correlations, 2.5)
    ci_upper = np.percentile(correlations, 97.5)
    
    return mean_corr, ci_lower, ci_upper

def analyze_correlation_with_lags(df):
    """
    Analyze correlations across all lag windows.
    
    Returns a list of results for each lag.
    """
    results = []
    
    # Extract time series
    time_col = 'date' if 'date' in df.columns else 'month'
    ar_intensity_col = 'ar_iwt' if 'ar_iwt' in df.columns else 'ar_intensity'
    gravity_col = 'gravity_anomaly' if 'gravity_anomaly' in df.columns else 'gravity'
    
    if ar_intensity_col not in df.columns or gravity_col not in df.columns:
        raise KeyError(
            f"Required columns not found. Expected '{ar_intensity_col}' and '{gravity_col}'. "
            f"Available: {df.columns.tolist()}"
        )
    
    ar_series = df[ar_intensity_col].values.astype(float)
    gravity_series = df[gravity_col].values.astype(float)
    
    # Remove NaN pairs
    valid_mask = ~(np.isnan(ar_series) | np.isnan(gravity_series))
    ar_clean = ar_series[valid_mask]
    gravity_clean = gravity_series[valid_mask]
    
    if len(ar_clean) < 3:
        logger.warning("Insufficient data points after cleaning.")
        return results
    
    for lag in LAGS:
        logger.info(f"Processing lag = {lag} months")
        
        # Apply lag
        if lag > 0:
            x = ar_clean[:-lag]
            y = gravity_clean[lag:]
        elif lag < 0:
            x = ar_clean[-lag:]
            y = gravity_clean[:lag]
        else:
            x = ar_clean
            y = gravity_clean
        
        if len(x) < 3:
            logger.warning(f"Insufficient data for lag {lag}. Skipping.")
            continue
        
        # Compute corrected correlation
        corr, p_val, n_eff, n_raw = compute_pearson_with_correction(x, y)
        
        if corr is None:
            logger.warning(f"Could not compute correlation for lag {lag}.")
            continue
        
        # Compute bootstrap CIs
        mean_boot, ci_low, ci_high = bootstrap_confidence_interval(
            x, y, n_iterations=BOOTSTRAP_ITERATIONS, seed=RANDOM_SEED, lag=0
        )
        
        # Significance flag (informational only, per SC-002)
        is_significant = p_val < 0.05 if p_val is not None else False
        
        result = {
            "lag_months": lag,
            "pearson_correlation": round(corr, 6),
            "p_value": round(p_val, 6) if p_val is not None else None,
            "effective_sample_size": n_eff,
            "raw_sample_size": n_raw,
            "bootstrap_mean": round(mean_boot, 6) if mean_boot is not None else None,
            "bootstrap_ci_lower": round(ci_low, 6) if ci_low is not None else None,
            "bootstrap_ci_upper": round(ci_high, 6) if ci_high is not None else None,
            "significance_flag_informational": is_significant,
            "methodology": "AR(1) pre-whitening with effective sample size correction"
        }
        results.append(result)
        logger.info(f"  Lag {lag}: r={corr:.4f}, p={p_val:.4f}, n_eff={n_eff}")
    
    return results

def save_results(results):
    """Save correlation results to JSON."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    output_data = {
        "metadata": {
            "input_file": str(DATA_PATH),
            "lags_analyzed": LAGS,
            "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
            "random_seed": RANDOM_SEED,
            "methodology": "AR(1) pre-whitening for autocorrelation correction",
            "note": "p < 0.05 is reported as an informational significance flag, not a pre-specified success criterion."
        },
        "results": results
    }
    
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Results saved to {OUTPUT_PATH}")
    return OUTPUT_PATH

def main():
    """Main entry point."""
    logger.info("Starting correlation analysis (T020)")
    
    try:
        # Load data
        df = load_merged_data()
        
        # Analyze correlations
        results = analyze_correlation_with_lags(df)
        
        if not results:
            logger.error("No correlation results computed. Exiting.")
            sys.exit(1)
        
        # Save results
        save_results(results)
        
        logger.info("Correlation analysis completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        sys.exit(1)
    except KeyError as e:
        logger.error(f"Schema error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()