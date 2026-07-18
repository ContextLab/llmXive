"""
Correlation analysis module for solar wind composition and geomagnetic indices.
Computes Pearson and Spearman coefficients at various lags, adjusts p-values
for autocorrelation (Neff), and applies Bonferroni correction.
"""
import os
import pandas as pd
import numpy as np
from scipy import stats
from datetime import timedelta
from typing import Dict, List, Tuple, Optional
from code import logger
from code.config import ACE_VARS, NOAA_VARS, TRAIN_START, TRAIN_END, TEST_START, TEST_END
from code.analysis.neff import calculate_neff

# Constants for lag analysis
LAGS_HOURS = [0, 1, 2, 3, 6]
OUTPUT_PATH = "data/processed/correlation_results.csv"
GLOBAL_THRESHOLD_PATH = "artifacts/thresholds/global_threshold.json"

def load_synced_data() -> pd.DataFrame:
    """
    Load the pre-aligned and interpolated dataset.
    Expects 'data/processed/synced.csv' to exist.
    """
    input_path = "data/processed/synced.csv"
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Synced data not found at {input_path}. "
            "Please run the US1 pipeline (T013/T016) first to generate this file."
        )
    
    logger.info(f"Loading synced data from {input_path}")
    df = pd.read_csv(input_path, parse_dates=['timestamp'])
    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    return df

def compute_correlations_at_lag(
    df: pd.DataFrame,
    ace_var: str,
    noaa_var: str,
    lag_hours: int
) -> Tuple[float, float, float, float, int, int]:
    """
    Compute Pearson and Spearman correlations for a specific ACE variable,
    NOAA variable, and time lag.
    
    Args:
        df: Synced dataframe with 'timestamp', ACE vars, and NOAA vars.
        ace_var: Name of the ACE variable (e.g., 'N_p').
        noaa_var: Name of the NOAA variable (e.g., 'Kp').
        lag_hours: Lag in hours (positive means ACE leads NOAA).
    
    Returns:
        Tuple of (pearson_r, spearman_r, raw_p, bonferroni_p, n_eff, n_obs)
    """
    # Shift ACE data forward by lag_hours to simulate leading
    # If lag > 0, we shift the ACE index forward (or NOAA backward)
    # To correlate ACE(t) with NOAA(t+lag), we shift ACE forward by lag
    # Implementation: Shift the ACE series forward by lag_hours relative to NOAA
    # Since the dataframe is sorted by time, we can shift the index or values.
    # Easier: Shift the ACE column values down by N rows where N = lag_hours * rows_per_hour.
    
    # Assuming 1-hour resolution
    shift_rows = lag_hours
    
    # Create shifted series
    # We want to correlate ACE(t) with NOAA(t+lag) -> ACE leads NOAA
    # So we compare ACE[t] with NOAA[t+lag]
    # This is equivalent to shifting NOAA backwards by lag, or ACE forwards.
    # Let's shift ACE forward: ACE_shifted[t] = ACE[t-lag]
    # Wait, standard lag definition: y(t) = f(x(t-lag)).
    # If we say "ACE leads NOAA by 1 hour", we expect ACE(t) to correlate with NOAA(t+1).
    # So we align ACE[t] with NOAA[t+1].
    # In a dataframe sorted by time:
    # Row i: ACE[i], NOAA[i]
    # We want to correlate ACE[i] with NOAA[i+lag].
    # So we take ACE[0:N-lag] and NOAA[lag:N].
    
    series_ace = df[ace_var].values
    series_noaa = df[noaa_var].values
    
    n = len(series_ace)
    if n <= shift_rows:
        logger.warning(f"Lag {lag_hours}h exceeds data length {n} rows. Skipping.")
        return (0.0, 0.0, 1.0, 1.0, 0, 0)
    
    ace_lagged = series_ace[:n-shift_rows]
    noaa_lagged = series_noaa[shift_rows:]
    
    # Remove NaNs resulting from any gaps or shifts
    mask = ~(np.isnan(ace_lagged) | np.isnan(noaa_lagged))
    ace_clean = ace_lagged[mask]
    noaa_clean = noaa_lagged[mask]
    
    if len(ace_clean) < 10:
        logger.warning(f"Not enough valid data points ({len(ace_clean)}) for correlation at lag {lag_hours}h.")
        return (0.0, 0.0, 1.0, 1.0, 0, len(ace_clean))
    
    # Compute Pearson
    pearson_r, pearson_p = stats.pearsonr(ace_clean, noaa_clean)
    
    # Compute Spearman
    spearman_r, spearman_p = stats.spearmanr(ace_clean, noaa_clean)
    
    # Calculate Neff for this specific pair (using the clean data length)
    # We apply the Neff correction to the p-values.
    # The formula in neff.py expects a series. We can use the ACE series as the primary driver
    # or average the Neff of both. Per FR-003/FR-010, we compute Neff based on the time series properties.
    # We will use the ACE series for Neff calculation as it represents the solar wind driver.
    neff = calculate_neff(pd.Series(ace_clean))
    
    # Adjust p-value for autocorrelation using Neff
    # For Pearson: p-value adjustment is complex, but often approximated by using Neff in the t-statistic
    # t = r * sqrt((N-2) / (1-r^2))
    # We replace N with Neff for the adjusted p-value calculation.
    # However, scipy.stats.pearsonr returns p based on N.
    # We recompute the p-value using the t-distribution with Neff.
    
    def adjust_pvalue(r, n_eff):
        if abs(r) >= 1.0:
            return 0.0 if r != 0 else 1.0
        t_stat = r * np.sqrt((n_eff - 2) / (1 - r**2))
        # Two-tailed test
        p_val = 2 * (1 - stats.t.cdf(abs(t_stat), df=n_eff - 2))
        return p_val
    
    # Apply Neff adjustment to Pearson p-value
    # Note: Spearman also assumes independence, so similar adjustment applies, 
    # but usually Pearson is the primary metric for this physics.
    # We will adjust the Pearson p-value.
    adjusted_p = adjust_pvalue(pearson_r, neff)
    
    return (float(pearson_r), float(spearman_r), float(adjusted_p), 0.0, int(neff), int(len(ace_clean)))

def run_correlation_analysis() -> pd.DataFrame:
    """
    Main entry point to run correlation analysis on the full dataset.
    Reads synced data, computes correlations for all pairs at all lags,
    applies Bonferroni correction, and saves results.
    
    Returns:
        DataFrame containing all correlation results.
    """
    logger.info("Starting correlation analysis (T020)...")
    
    # Load data
    df = load_synced_data()
    
    # Ensure we have the required columns
    required_cols = ACE_VARS + NOAA_VARS
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in synced data: {missing}")
    
    results = []
    
    # Calculate global Bonferroni divisor
    # 3 params * 2 indices * 5 lags = 30
    total_tests = len(ACE_VARS) * len(NOAA_VARS) * len(LAGS_HOURS)
    bonferroni_alpha = 0.05 / total_tests
    
    logger.info(f"Total tests: {total_tests}, Bonferroni alpha: {bonferroni_alpha}")
    
    for ace_var in ACE_VARS:
        for noaa_var in NOAA_VARS:
            for lag in LAGS_HOURS:
                logger.info(f"Computing correlation: {ace_var} vs {noaa_var} at lag {lag}h")
                
                pearson_r, spearman_r, raw_p, _, neff, n_obs = compute_correlations_at_lag(
                    df, ace_var, noaa_var, lag
                )
                
                # Apply Bonferroni correction to the raw (Neff-adjusted) p-value
                # p_bonf = p_raw * total_tests, capped at 1.0
                bonferroni_p = min(raw_p * total_tests, 1.0)
                
                is_significant = bonferroni_p < 0.05
                is_strong = abs(pearson_r) > 0.5
                
                results.append({
                    'ace_variable': ace_var,
                    'noaa_variable': noaa_var,
                    'lag_hours': lag,
                    'pearson_r': pearson_r,
                    'spearman_r': spearman_r,
                    'p_value_raw_neff': raw_p,
                    'p_value_bonferroni': bonferroni_p,
                    'n_eff': neff,
                    'n_observations': n_obs,
                    'is_significant': is_significant,
                    'is_strong': is_strong
                })
    
    # Create DataFrame
    results_df = pd.DataFrame(results)
    
    # Save to CSV
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    results_df.to_csv(OUTPUT_PATH, index=False)
    logger.info(f"Correlation results saved to {OUTPUT_PATH}")
    
    # Log summary
    significant_count = results_df['is_significant'].sum()
    strong_count = results_df['is_strong'].sum()
    logger.info(f"Analysis complete. Significant pairs: {significant_count}, Strong pairs (|r|>0.5): {strong_count}")
    
    return results_df

# Backward compatibility for direct imports if needed
if __name__ == "__main__":
    run_correlation_analysis()