import os
import pandas as pd
import numpy as np
from scipy import stats
from datetime import timedelta
from typing import Dict, List, Tuple, Optional
from code.config import ACE_VARS, NOAA_VARS, TRAIN_START, TRAIN_END, TEST_START, TEST_END
from code import logger
from code.analysis.neff import calculate_neff

# Configuration for Bonferroni correction
# 3 ACE parameters (N_p, T_p, He2+_ratio)
# 2 NOAA indices (Kp, Dst)
# 5 lags (0, 1, 2, 3, 6 hours)
N_PARAMS = len(ACE_VARS)
N_INDICES = len(NOAA_VARS)
N_LAGS = 5  # 0, 1, 2, 3, 6
TOTAL_TESTS = N_PARAMS * N_INDICES * N_LAGS
ALPHA_RAW = 0.05
ALPHA_ADJ = ALPHA_RAW / TOTAL_TESTS

logger.info(f"Bonferroni configuration: {N_PARAMS} params x {N_INDICES} indices x {N_LAGS} lags = {TOTAL_TESTS} tests")
logger.info(f"Adjusted alpha (Bonferroni): {ALPHA_ADJ:.6f}")

def load_synced_data() -> pd.DataFrame:
    """Load the synchronized dataset from the processed directory."""
    path = "data/processed/synced.csv"
    if not os.path.exists(path):
        raise FileNotFoundError(f"Synced data not found at {path}. Run US1 pipeline first.")
    df = pd.read_csv(path, parse_dates=['timestamp'])
    logger.info(f"Loaded synced data: {df.shape[0]} rows, {df.shape[1]} columns")
    return df

def compute_correlations_at_lag(
    df: pd.DataFrame,
    param: str,
    index_var: str,
    lag_hours: int,
    neff: Optional[float] = None
) -> Dict:
    """
    Compute Pearson and Spearman correlations for a specific parameter, index, and lag.
    
    Args:
        df: The synchronized dataframe.
        param: The ACE parameter name (e.g., 'N_p').
        index_var: The NOAA index name (e.g., 'Kp').
        lag_hours: The lag in hours (0, 1, 2, 3, 6).
        neff: Optional pre-calculated effective sample size. If None, calculated from data.
    
    Returns:
        Dictionary containing correlation metrics.
    """
    if lag_hours > 0:
        # Shift the ACE data forward by lag_hours to simulate lagged effect
        # If lag is positive, we align ACE(t) with Index(t+lag)
        # In the dataframe, we shift the ACE column down by lag_hours
        shift_rows = lag_hours
        if shift_rows > 0:
            df_shifted = df.copy()
            df_shifted[param] = df_shifted[param].shift(shift_rows)
            # Drop rows where the shifted value is NaN (the beginning of the series)
            df_valid = df_shifted.dropna(subset=[param, index_var])
        else:
            df_valid = df
    else:
        df_valid = df.dropna(subset=[param, index_var])

    if len(df_valid) < 10:
        logger.warning(f"Insufficient data for {param} vs {index_var} at lag {lag_hours}h: {len(df_valid)} rows")
        return {
            'param': param,
            'index': index_var,
            'lag': lag_hours,
            'pearson_r': np.nan,
            'spearman_rho': np.nan,
            'p_value_raw': np.nan,
            'p_value_bonferroni': np.nan,
            'n_obs': len(df_valid),
            'neff': np.nan,
            'is_significant': False
        }

    x = df_valid[param].values
    y = df_valid[index_var].values

    # Pearson
    r, p_raw = stats.pearsonr(x, y)
    
    # Spearman
    rho, p_spearman = stats.spearmanr(x, y)

    # Calculate Neff if not provided
    if neff is None:
        # We calculate Neff based on the overlapping valid data length
        # However, the spec implies Neff is calculated on the FULL continuous series.
        # For this function, we calculate it on the valid subset for accuracy in this specific window,
        # but the main runner should ideally pass the global Neff or calculate it globally.
        # Per T021, we use the Pyper & Peterman method on the residuals.
        # Since we are in a generic function, we calculate it here on the valid data for this pair.
        # NOTE: The global Neff calculation is handled in run_correlation_analysis for consistency.
        # Here we compute a local estimate if not passed, but the global one is preferred for the threshold.
        neff_local = calculate_neff(x)
    else:
        neff_local = neff

    # Adjust p-value for Neff? 
    # The spec says: "adjust p-values for autocorrelation (Neff)".
    # Standard approach: Use Neff to adjust the degrees of freedom in the t-test for correlation significance.
    # t = r * sqrt((Neff - 2) / (1 - r^2))
    # But scipy.stats.pearsonr uses N-2. We can approximate the adjusted p-value by re-calculating it.
    
    if not np.isnan(r) and neff_local > 2:
        t_stat = r * np.sqrt((neff_local - 2) / (1 - r**2 + 1e-10))
        # Two-tailed p-value
        p_adj = 2 * (1 - stats.t.cdf(abs(t_stat), neff_local - 2))
    else:
        p_adj = p_raw

    # Bonferroni correction
    p_bonf = min(p_adj * TOTAL_TESTS, 1.0)
    is_significant = p_bonf < ALPHA_ADJ

    logger.debug(f"Lag {lag_hours}h: {param} vs {index_var}, r={r:.4f}, p_raw={p_adj:.4e}, p_bonf={p_bonf:.4e}, sig={is_significant}")

    return {
        'param': param,
        'index': index_var,
        'lag': lag_hours,
        'pearson_r': r,
        'spearman_rho': rho,
        'p_value_raw': p_adj,
        'p_value_bonferroni': p_bonf,
        'n_obs': len(df_valid),
        'neff': neff_local,
        'is_significant': is_significant
    }

def run_correlation_analysis(df: Optional[pd.DataFrame] = None, output_path: str = "data/processed/correlation_results.csv") -> pd.DataFrame:
    """
    Run the full correlation analysis across all parameters, indices, and lags.
    Implements FR-004: Bonferroni correction with dynamic divisor 30.
    
    Args:
        df: Optional dataframe. If None, loads from disk.
        output_path: Path to save the results CSV.
    
    Returns:
        DataFrame with all correlation results.
    """
    if df is None:
        df = load_synced_data()

    results = []
    
    # Define lags explicitly
    lags = [0, 1, 2, 3, 6]

    logger.info(f"Starting correlation analysis for {len(ACE_VARS)} params x {len(NOAA_VARS)} indices x {len(lags)} lags")
    logger.info(f"Using Bonferroni divisor: {TOTAL_TESTS} (Alpha adjusted to {ALPHA_ADJ})")

    # Pre-calculate global Neff for the full series if possible, or per variable
    # The spec emphasizes global Neff for the threshold. 
    # We will calculate Neff for each ACE variable on the full series (ignoring NaNs in the specific column)
    # to use as the 'neff' argument for the correlation functions, ensuring consistency.
    global_neff_map = {}
    for var in ACE_VARS:
        if var in df.columns:
            clean_series = df[var].dropna()
            if len(clean_series) > 10:
                global_neff_map[var] = calculate_neff(clean_series.values)
            else:
                global_neff_map[var] = None
        else:
            global_neff_map[var] = None

    for param in ACE_VARS:
        if param not in df.columns:
            logger.warning(f"ACE variable {param} not found in data, skipping.")
            continue

        for index_var in NOAA_VARS:
            if index_var not in df.columns:
                logger.warning(f"NOAA variable {index_var} not found in data, skipping.")
                continue
            
            neff_for_param = global_neff_map.get(param)

            for lag in lags:
                res = compute_correlations_at_lag(
                    df, 
                    param, 
                    index_var, 
                    lag,
                    neff=neff_for_param
                )
                results.append(res)

    results_df = pd.DataFrame(results)
    
    # Sort for readability
    results_df = results_df.sort_values(by=['param', 'index', 'lag'])

    # Save to disk
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    results_df.to_csv(output_path, index=False)
    logger.info(f"Correlation results saved to {output_path}")
    logger.info(f"Significant findings (Bonferroni p < {ALPHA_ADJ}): {results_df['is_significant'].sum()}")

    return results_df

# Export for main.py
__all__ = ['load_synced_data', 'compute_correlations_at_lag', 'run_correlation_analysis', 'ALPHA_ADJ', 'TOTAL_TESTS']
