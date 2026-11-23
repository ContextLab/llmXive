import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, t
from statsmodels.tsa.ar_model import AutoReg
from statsmodels.stats.multitest import multipletests
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_merged_data(path: str) -> pd.DataFrame:
    """Load the merged monthly dataset."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Merged data file not found: {path}. Run T017c first.")
    df = pd.read_csv(path, parse_dates=["date"])
    logger.info(f"Loaded merged data with {len(df)} rows.")
    return df

def calculate_effective_sample_size(n: int, rho: float) -> float:
    """Calculate effective sample size for autocorrelated data."""
    if abs(rho) >= 1:
        return 1
    return n * (1 - rho) / (1 + rho)

def prewhiten_series(series: np.ndarray) -> np.ndarray:
    """Pre-whiten series using AR(1) model."""
    if len(series) < 5:
        logger.warning("Series too short for pre-whitening, returning original.")
        return series
    try:
        model = AutoReg(series, lags=1, old_names=False)
        res = model.fit()
        return res.resid
    except Exception as e:
        logger.warning(f"Pre-whitening failed: {e}. Returning original series.")
        return series

def bootstrap_confidence_interval(x: np.ndarray, y: np.ndarray, iterations: int = 1000, seed: int = 42) -> Tuple[float, float]:
    """Bootstrap resampling to estimate 95% CI for Pearson r."""
    np.random.seed(seed)
    n = len(x)
    boot_r = []
    for _ in range(iterations):
        idx = np.random.choice(n, n, replace=True)
        r, _ = pearsonr(x[idx], y[idx])
        boot_r.append(r)
    return np.percentile(boot_r, [2.5, 97.5])

def newey_west_standard_error(r: float, n: int, lags: int = 1) -> float:
    """
    Approximate Newey-West adjustment for standard error.
    This implementation uses a heuristic based on effective sample size
    derived from the lag-1 autocorrelation of the residuals of a simple regression.
    """
    if n <= 2:
        return 1.0
    
    # Calculate autocorrelation of residuals (simplified approach)
    # In a full implementation, we would fit a model and check residuals
    # Here we estimate rho from the series themselves as a proxy for residual autocorrelation
    if n > 2:
        rho = np.corrcoef(series[:-1], series[1:])[0, 1] if (series := np.concatenate([x, y])) is not None else 0.0
    else:
        rho = 0.0
        
    n_eff = calculate_effective_sample_size(n, rho)
    
    # Standard error of r
    se = np.sqrt((1 - r**2) / (n_eff - 2))
    return se

def compute_pearson_with_correction(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """Compute Pearson correlation and raw p-value."""
    if len(x) < 3:
        return 0.0, 1.0
    r, p_raw = pearsonr(x, y)
    return r, p_raw

def analyze_correlation_with_lags(
    df: pd.DataFrame, 
    region_type: str, 
    lags: List[int] = [-3, -2, -1, 0, 1, 2, 3]
) -> Tuple[pd.DataFrame, float]:
    """Analyze correlation for a specific region across multiple lags."""
    results = []
    raw_ps = []
    
    if len(df) < 10:
        logger.warning(f"Region {region_type} has too few data points ({len(df)}). Skipping.")
        return pd.DataFrame(), 0.0

    # Pre-whiten both series
    ar_series = prewhiten_series(df["ar_intensity"].values)
    grav_series = prewhiten_series(df["gravity_anomaly"].values)

    # Calculate noise floor (3 sigma)
    mean_uncertainty = df["uncertainty"].mean() if "uncertainty" in df.columns else 1.0
    noise_floor = 3 * mean_uncertainty

    for lag in lags:
        if lag > 0:
            x = ar_series[:-lag]
            y = grav_series[lag:]
        elif lag < 0:
            x = ar_series[-lag:]
            y = grav_series[:lag]
        else:
            x, y = ar_series, grav_series

        if len(x) < 5:
            continue  # insufficient points

        r, p_raw = compute_pearson_with_correction(x, y)
        raw_ps.append(p_raw)

        # Bootstrap CI
        ci_low, ci_high = bootstrap_confidence_interval(x, y)

        # Signal to Noise Ratio
        snr = r / mean_uncertainty if mean_uncertainty != 0 else 0.0

        # 3 Sigma Threshold Check
        # We check if the magnitude of the correlation is significant relative to noise
        # Note: The spec asks for signal magnitude relative to noise floor (>= 3 sigma)
        # Here we interpret this as: is the SNR >= 3?
        passes_threshold = abs(snr) >= 3.0

        results.append({
            "lag": lag,
            "correlation_coefficient": r,
            "raw_p_value": p_raw,
            "confidence_interval_lower": ci_low,
            "confidence_interval_upper": ci_high,
            "region_type": region_type,
            "signal_to_noise_ratio": snr,
            "passes_3sigma_threshold": passes_threshold
        })

    # FDR Correction
    if raw_ps:
        _, p_corr, _, _ = multipletests(raw_ps, method="fdr_bh")
        for i, res in enumerate(results):
            res["corrected_p_value"] = p_corr[i]
    else:
        for res in results:
            res["corrected_p_value"] = 1.0

    return pd.DataFrame(results), noise_floor

def save_results(results_df: pd.DataFrame, out_path: str) -> None:
    """Save results to CSV."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    results_df.to_csv(out_path, index=False)
    logger.info(f"Correlation analysis complete. Results saved to {out_path}")

def main():
    merged_path = "data/processed/merged_monthly.csv"
    out_path = "data/processed/correlation_results.csv"
    
    logger.info("Starting correlation analysis...")
    
    if not os.path.exists(merged_path):
        logger.critical(f"Merged data file not found: {merged_path}. Run T017c first.")
        sys.exit(1)

    df = load_merged_data(merged_path)

    target_df = df[df["region"] == "target"]
    control_df = df[df["region"] == "control"]

    if target_df.empty:
        logger.warning("No target region data found.")
    else:
        target_results, _ = analyze_correlation_with_lags(target_df, "target")
    
    if control_df.empty:
        logger.warning("No control region data found.")
    else:
        control_results, _ = analyze_correlation_with_lags(control_df, "control")

    # Combine results
    all_results = pd.concat([target_results, control_results], ignore_index=True) if not target_results.empty and not control_results.empty else target_results if not target_results.empty else control_results

    if all_results.empty:
        logger.error("No results generated. Check data availability.")
        sys.exit(1)

    save_results(all_results, out_path)

if __name__ == "__main__":
    main()