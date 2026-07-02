"""
Significance testing utilities for lagged correlations.

Includes logic for:
- Local Neff calculation (for validation sets)
- Re-computing Bonferroni p-values for specific subsets (T023b, T032a)
"""
import numpy as np
import pandas as pd
from scipy import stats, signal
from typing import List, Dict, Tuple, Optional
from code.config import ACE_VARS, NOAA_VARS, TEST_START, TEST_END
from code import logger


def calculate_local_neff_and_pvalue(
    x: pd.Series, 
    y: pd.Series, 
    lag: int = 0,
    alpha: float = 0.05,
    n_tests: int = 30
) -> Dict:
    """
    Calculate Neff and p-value for a specific pair of series, optionally with lag.
    
    This function is designed to be run on subsets (e.g., validation set) to verify
    stability of correlations. It applies the Pyper & Peterman method:
    1. Detrend both series.
    2. Calculate lag-1 autocorrelation of residuals for x and y to get rho1_x, rho1_y.
    3. Estimate Neff.
    4. Calculate t-statistic and p-value.
    5. Apply Bonferroni correction using the provided n_tests.
    
    Args:
        x: First time series (e.g., He2+_ratio)
        y: Second time series (e.g., Dst)
        lag: Lag in hours to apply to y relative to x (y is shifted)
        alpha: Significance level
        n_tests: Number of tests in the family for Bonferroni correction (default 30)
    
    Returns:
        Dictionary with Neff, raw p-value, Bonferroni p-value, and significance flag.
    """
    if len(x) != len(y):
        raise ValueError("Series x and y must have the same length.")
    
    # Apply lag
    if lag > 0:
        y_shifted = y.shift(lag)
    elif lag < 0:
        y_shifted = y.shift(-lag) # Assuming lag definition: x(t) vs y(t+lag)
    else:
        y_shifted = y
    
    # Drop NaNs resulting from lag or original data
    valid_mask = ~y_shifted.isna() & ~x.isna()
    x_valid = x[valid_mask]
    y_valid = y_shifted[valid_mask]
    
    if len(x_valid) < 10:
        logger.warning(f"Insufficient data points after lagging ({len(x_valid)}). Skipping.")
        return {
            "n_eff": None,
            "r": None,
            "p_raw": None,
            "p_bonferroni": None,
            "significant": False
        }
    
    # Step 1: Detrend
    x_detrended = signal.detrend(x_valid.values)
    y_detrended = signal.detrend(y_valid.values)
    
    # Step 2: Calculate lag-1 autocorrelation of residuals
    # rho1 = corr(resid_t, resid_{t-1})
    def get_rho1(resid):
        if len(resid) < 2:
            return 0.0
        return np.corrcoef(resid[:-1], resid[1:])[0, 1]
    
    rho1_x = get_rho1(x_detrended)
    rho1_y = get_rho1(y_detrended)
    
    # Handle NaN correlations (e.g., constant series)
    if np.isnan(rho1_x): rho1_x = 0.0
    if np.isnan(rho1_y): rho1_y = 0.0
    
    # Step 3: Estimate Neff
    # Using the formula: Neff = N * (1 - rho1) / (1 + rho1)
    # For two series, we can use an average or the product method. 
    # Pyper & Peterman often use the average of the two rho1s or the product.
    # A common approximation for two series is to use the geometric mean or average.
    # Let's use the average of the two rho1 values for the Neff calculation.
    rho1_avg = (rho1_x + rho1_y) / 2.0
    
    # Ensure rho1 is within (-1, 1) to avoid division by zero or negative Neff
    rho1_avg = np.clip(rho1_avg, -0.99, 0.99)
    
    N = len(x_valid)
    neff = N * (1 - rho1_avg) / (1 + rho1_avg)
    
    # Step 4: Calculate Pearson correlation and p-value using Neff
    r, p_raw = stats.pearsonr(x_valid, y_valid)
    
    # Adjust p-value using Neff
    # The t-statistic is t = r * sqrt((Neff - 2) / (1 - r^2))
    if abs(r) >= 1.0:
        p_adj = 0.0 if r != 0 else 1.0
    else:
        t_stat = r * np.sqrt((neff - 2) / (1 - r**2))
        # Two-tailed p-value
        p_adj = 2 * (1 - stats.t.cdf(abs(t_stat), df=neff - 2))
    
    # Step 5: Bonferroni correction
    p_bonferroni = min(p_adj * n_tests, 1.0)
    significant = p_bonferroni < alpha
    
    return {
        "n_eff": neff,
        "rho1_x": rho1_x,
        "rho1_y": rho1_y,
        "r": r,
        "p_raw": p_raw,
        "p_bonferroni": p_bonferroni,
        "significant": significant
    }


def run_validation_significance(
    df_synced: pd.DataFrame,
    lags: List[int] = [0, 1, 2, 3, 6]
) -> pd.DataFrame:
    """
    Run significance analysis on the validation set (2018-2020).
    
    This function:
    1. Filters df_synced to the test period (TEST_START to TEST_END).
    2. Iterates through all ACE x NOAA pairs and lags.
    3. Calculates local Neff and Bonferroni p-values for each pair.
    4. Returns a DataFrame of results.
    
    Args:
        df_synced: Full synced dataframe with 'timestamp' column.
        lags: List of lags to test.
    
    Returns:
        DataFrame with columns: var_x, var_y, lag, r, n_eff, p_raw, p_bonferroni, significant
    """
    # Filter to test period
    mask = (df_synced['timestamp'].dt.year >= TEST_START) & (df_synced['timestamp'].dt.year <= TEST_END)
    df_test = df_synced[mask].copy()
    
    if df_test.empty:
        logger.warning("No data found in the validation period (2018-2020).")
        return pd.DataFrame()
    
    logger.info(f"Running validation significance on {len(df_test)} rows (2018-2020).")
    
    results = []
    n_tests_total = 30 # Fixed global divisor as per T023
    
    for var_x in ACE_VARS:
        for var_y in NOAA_VARS:
            if var_x not in df_test.columns or var_y not in df_test.columns:
                continue
            
            for lag in lags:
                res = calculate_local_neff_and_pvalue(
                    df_test[var_x], 
                    df_test[var_y], 
                    lag=lag,
                    n_tests=n_tests_total
                )
                
                results.append({
                    "var_x": var_x,
                    "var_y": var_y,
                    "lag": lag,
                    "r": res['r'],
                    "n_eff": res['n_eff'],
                    "p_raw": res['p_raw'],
                    "p_bonferroni": res['p_bonferroni'],
                    "significant": res['significant']
                })
    
    return pd.DataFrame(results)