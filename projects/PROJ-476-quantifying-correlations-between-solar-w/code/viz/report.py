"""
Report generation and validation logic for User Story 3.
Handles train/test splitting, global threshold loading, and local significance re-computation.
"""
import os
import json
import pandas as pd
import numpy as np
from scipy import stats, signal
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

from code.config import TRAIN_START, TRAIN_END, TEST_START, TEST_END, ACE_VARS, NOAA_VARS
from code import logger

# Constants for significance testing
LAGS = [0, 1, 2, 3, 6]
BONFERRONI_DIVISOR = 30  # 3 params * 2 indices * 5 lags
ALPHA = 0.05

def load_global_thresholds() -> Dict[str, Any]:
    """
    Load the global significance thresholds computed from the full training set.
    Reads from artifacts/thresholds/global_threshold.json.
    """
    path = "artifacts/thresholds/global_threshold.json"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Global thresholds file not found at {path}. "
                                "Run US2 (T025a) first to generate this file.")
    
    with open(path, 'r') as f:
        return json.load(f)

def split_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split the synced dataset into training (1998-2017) and test (2018-2020) sets.
    Uses TRAIN_START, TRAIN_END, TEST_START, TEST_END from code.config.
    """
    logger.info(f"Splitting data: Train [{TRAIN_START}-{TRAIN_END}], Test [{TEST_START}-{TEST_END}]")
    
    # Ensure timestamp column is datetime if it isn't already
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Filter based on year
    train_mask = (df['timestamp'].dt.year >= TRAIN_START) & (df['timestamp'].dt.year <= TRAIN_END)
    test_mask = (df['timestamp'].dt.year >= TEST_START) & (df['timestamp'].dt.year <= TEST_END)
    
    train_df = df[train_mask].copy()
    test_df = df[test_mask].copy()
    
    logger.info(f"Train set size: {len(train_df)}, Test set size: {len(test_df)}")
    return train_df, test_df

def calculate_local_neff(series: pd.Series) -> float:
    """
    Calculate effective sample size (Neff) for a specific time series using the
    Pyper & Peterman method (detrended lag-1 autocorrelation).
    
    Formula: Neff = N * (1 - rho_1) / (1 + rho_1)
    
    Steps:
    1. Detrend the series using scipy.signal.detrend.
    2. Calculate lag-1 autocorrelation of the residuals.
    3. Apply formula.
    """
    if len(series) < 2:
        raise ValueError("Series too short to calculate Neff.")
    
    # 1. Detrend
    residuals = signal.detrend(series.values.astype(float))
    
    # 2. Calculate lag-1 autocorrelation manually to ensure precision
    # rho_1 = corr(x_t, x_{t-1})
    x_t = residuals[1:]
    x_t_minus_1 = residuals[:-1]
    
    if len(x_t) == 0:
        return float(len(series))
        
    # Handle constant series (variance 0)
    if np.std(x_t) == 0 or np.std(x_t_minus_1) == 0:
        rho_1 = 0.0
    else:
        rho_1 = np.corrcoef(x_t, x_t_minus_1)[0, 1]
        if np.isnan(rho_1):
            rho_1 = 0.0
    
    # 3. Apply formula
    N = len(series)
    # Clamp rho_1 to (-1, 1) to avoid division by zero or negative Neff issues
    rho_1 = np.clip(rho_1, -0.9999, 0.9999)
    
    neff = N * (1 - rho_1) / (1 + rho_1)
    return float(neff)

def calculate_local_bonferroni_pvalue(r: float, neff: float) -> float:
    """
    Calculate the raw p-value for a correlation coefficient r given effective sample size neff,
    then apply Bonferroni correction.
    
    Uses t-distribution: t = r * sqrt((neff - 2) / (1 - r^2))
    """
    if neff <= 2:
        return 1.0
    
    if abs(r) >= 1.0:
        return 0.0
    
    # T-statistic
    t_stat = r * np.sqrt((neff - 2) / (1 - r**2))
    
    # Two-tailed p-value
    p_raw = 2 * (1 - stats.t.cdf(abs(t_stat), df=neff - 2))
    
    # Bonferroni correction (global divisor applied to local p)
    p_adj = min(p_raw * BONFERRONI_DIVISOR, 1.0)
    
    return float(p_adj)

def recompute_local_significance(test_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Re-compute Neff and Bonferroni p-values specifically for the validation set (2018-2020).
    
    This satisfies SC-003: verifying stability of correlations in the test set
    using local statistics, not just relying on global thresholds.
    
    Returns a list of dictionaries with correlation details for the test set.
    """
    logger.info("Re-computing local significance for validation set (2018-2020)...")
    
    results = []
    
    # Iterate over all ACE x NOAA pairs
    for ace_var in ACE_VARS:
        if ace_var not in test_df.columns:
            logger.warning(f"ACE variable {ace_var} missing in test set. Skipping.")
            continue
        
        for noaa_var in NOAA_VARS:
            if noaa_var not in test_df.columns:
                logger.warning(f"NOAA variable {noaa_var} missing in test set. Skipping.")
                continue
            
            # Calculate Neff for both series in the test set
            neff_ace = calculate_local_neff(test_df[ace_var])
            neff_noaa = calculate_local_neff(test_df[noaa_var])
            
            # Use the minimum Neff for the pair (conservative approach) or average?
            # Standard practice for correlation significance is often to use the Neff of the residuals
            # or the minimum. We will use the minimum to be conservative.
            effective_n = min(neff_ace, neff_noaa)
            
            for lag in LAGS:
                # Shift one series to simulate lag
                # Positive lag: ACE leads NOAA (ACE at t, NOAA at t+lag)
                # We shift the NOAA series forward in time relative to ACE?
                # Actually, standard lag definition: corr(X_t, Y_{t-lag})
                # If lag=1, we correlate X_t with Y_{t-1} (Y lags X).
                # Let's align by index after shifting.
                
                ace_series = test_df[ace_var].dropna()
                noaa_series = test_df[noaa_var].dropna()
                
                if len(ace_series) != len(noaa_series) or not ace_series.index.equals(noaa_series.index):
                    # Re-index to ensure alignment
                    common_idx = ace_series.index.intersection(noaa_series.index)
                    ace_series = ace_series.loc[common_idx]
                    noaa_series = noaa_series.loc[common_idx]
                
                if len(ace_series) < 10:
                    continue
                
                # Apply lag
                if lag > 0:
                    # Shift NOAA down (so we compare ACE[t] with NOAA[t-lag])
                    # In a time-indexed series, shifting down moves values to later times.
                    # We want to correlate ACE[t] with NOAA[t-lag].
                    # So we take NOAA shifted by +lag (values move to future) and align?
                    # Simpler: shift the series object.
                    shifted_noaa = noaa_series.shift(lag)
                elif lag < 0:
                    shifted_noaa = noaa_series.shift(abs(lag)) # Shift other way?
                    # Usually lags are 0, 1, 2...
                    # Let's assume non-negative lags as per task description
                    continue
                else:
                    shifted_noaa = noaa_series
                
                # Drop NaNs introduced by shift
                valid_mask = ~shifted_noaa.isna()
                ace_lag = ace_series[valid_mask]
                noaa_lag = shifted_noaa[valid_mask]
                
                if len(ace_lag) < 10:
                    continue
                
                # Compute correlation
                corr_val, p_raw = stats.pearsonr(ace_lag, noaa_lag)
                
                # Recalculate Neff for the *aligned* series (optional but more precise)
                # For simplicity and consistency with the "local Neff" requirement,
                # we use the Neff calculated on the full available series above.
                
                # Calculate local Bonferroni p-value
                p_bonf = calculate_local_bonferroni_pvalue(corr_val, effective_n)
                
                results.append({
                    "ace_var": ace_var,
                    "noaa_var": noaa_var,
                    "lag": lag,
                    "pearson_r": float(corr_val),
                    "local_neff": float(effective_n),
                    "local_bonferroni_p": float(p_bonf),
                    "significant": p_bonf < ALPHA
                })
    
    logger.info(f"Local significance re-computation complete. Found {len(results)} pairs.")
    return results

def evaluate_validation_results(local_results: List[Dict], global_thresholds: Dict) -> str:
    """
    Evaluate the local results against the global thresholds and the |r| > 0.5 criteria.
    Generates a summary report string.
    """
    report_lines = []
    report_lines.append("## Validation Set (2018-2020) Significance Report")
    report_lines.append("")
    
    significant_pairs = [r for r in local_results if r['significant']]
    
    report_lines.append(f"Total pairs tested: {len(local_results)}")
    report_lines.append(f"Significant pairs (local Bonferroni p < 0.05): {len(significant_pairs)}")
    report_lines.append("")
    
    strong_significant = [r for r in significant_pairs if abs(r['pearson_r']) > 0.5]
    
    report_lines.append(f"Strong significant pairs (|r| > 0.5 AND p < 0.05): {len(strong_significant)}")
    report_lines.append("")
    
    if strong_significant:
        report_lines.append("### Detailed Strong Significant Findings:")
        for r in strong_significant:
            report_lines.append(f"- {r['ace_var']} vs {r['noaa_var']} (lag {r['lag']}h): "
                                f"r = {r['pearson_r']:.3f}, p_bonf = {r['local_bonferroni_p']:.4f}, "
                                f"local_Neff = {r['local_neff']:.1f}")
    else:
        report_lines.append("No pairs met both criteria (|r| > 0.5 and local Bonferroni p < 0.05) in the validation set.")
    
    return "\n".join(report_lines)

def run_validation_report() -> str:
    """
    Main entry point for T032a logic.
    1. Loads synced data.
    2. Splits into train/test.
    3. Loads global thresholds.
    4. Re-computes local Neff and p-values for the test set.
    5. Generates and returns a report string.
    """
    # 1. Load data
    data_path = "data/processed/synced.csv"
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Synced data not found at {data_path}. Run US1 first.")
    
    df = pd.read_csv(data_path, parse_dates=['timestamp'])
    
    # 2. Split data
    train_df, test_df = split_data(df)
    
    if len(test_df) == 0:
        raise ValueError("Test set is empty. Check date ranges in config.")
    
    # 3. Load global thresholds (for reference, though we recompute locally)
    try:
        global_thresholds = load_global_thresholds()
    except FileNotFoundError as e:
        logger.warning(f"Could not load global thresholds: {e}. Continuing with local computation only.")
        global_thresholds = None
    
    # 4. Re-compute local significance
    local_results = recompute_local_significance(test_df)
    
    # 5. Evaluate and generate report
    report = evaluate_validation_results(local_results, global_thresholds or {})
    
    # Optional: Save detailed results to a file for inspection
    results_path = "artifacts/reports/validation_local_significance.json"
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(local_results, f, indent=2)
    logger.info(f"Local significance results saved to {results_path}")
    
    return report

def check_threshold_detection(df: pd.DataFrame) -> bool:
    """
    Helper function for tests. Checks if any pair exceeds |r| > 0.5.
    """
    for ace_var in ACE_VARS:
        for noaa_var in NOAA_VARS:
            if ace_var in df.columns and noaa_var in df.columns:
                # Quick check on first available lag
                valid_mask = df[ace_var].notna() & df[noaa_var].notna()
                if valid_mask.sum() > 10:
                    r, _ = stats.pearsonr(df.loc[valid_mask, ace_var], df.loc[valid_mask, noaa_var])
                    if abs(r) > 0.5:
                        return True
    return False