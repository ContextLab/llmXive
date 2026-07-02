import os
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Optional
from code import logger
from code.config import TRAIN_START, TRAIN_END, TEST_START, TEST_END
from code.analysis.neff import calculate_neff
from code.analysis.significance import compute_pvalue_with_neff, calculate_neff_for_subset

# Global Bonferroni divisor: 3 parameters (N_p, T_p, He2+_ratio) * 2 indices (Kp, Dst) * 5 lags (0,1,2,3,6)
BONFERRONI_DIVISOR = 30
ALPHA = 0.05
BONFERRONI_THRESHOLD = ALPHA / BONFERRONI_DIVISOR

def compute_correlation_at_lag(df: pd.DataFrame, var_x: str, var_y: str, lag_hours: int) -> Tuple[float, float, float]:
    """
    Compute Pearson and Spearman correlations between var_x and var_y at a specific lag.
    var_x is shifted by lag_hours (positive lag means var_x leads var_y).
    
    Returns: (pearson_r, spearman_rho, p_value_raw)
    """
    if lag_hours > 0:
        shifted_x = df[var_x].shift(lag_hours)
    elif lag_hours < 0:
        shifted_x = df[var_x].shift(-lag_hours) # Shift other way if negative lag needed, though spec implies positive
    else:
        shifted_x = df[var_x]
    
    # Drop NaNs resulting from shift
    valid_mask = shifted_x.notna() & df[var_y].notna()
    x_valid = shifted_x[valid_mask]
    y_valid = df[var_y][valid_mask]
    
    if len(x_valid) < 10:
        logger.warning(f"Not enough data points for correlation at lag {lag_hours} for {var_x} vs {var_y}")
        return np.nan, np.nan, np.nan
    
    pearson_r, p_pearson = stats.pearsonr(x_valid, y_valid)
    spearman_rho, p_spearman = stats.spearmanr(x_valid, y_valid)
    
    # Return raw p-value (unadjusted for Neff yet, will be adjusted in next step)
    # We use the p-value from the test statistic but the significance check will use Neff-adjusted p
    return float(pearson_r), float(spearman_rho), float(p_pearson)

def compute_neff_adjusted_pvalue(r: float, n: int, rho1: float) -> float:
    """
    Compute p-value adjusted for autocorrelation using Neff.
    Uses the formula for Neff and then computes p-value from t-distribution.
    """
    neff = calculate_neff(n, rho1)
    if neff <= 2:
        return 1.0
    
    # t-statistic for correlation: t = r * sqrt((neff - 2) / (1 - r^2))
    if abs(r) >= 1.0:
        return 0.0 if r != 0 else 1.0
        
    t_stat = r * np.sqrt((neff - 2) / (1 - r**2))
    # Two-tailed p-value
    p_val = 2 * (1 - stats.t.cdf(abs(t_stat), neff - 2))
    return float(p_val)

def apply_bonferroni_correction(raw_p: float) -> float:
    """
    Apply Bonferroni correction to a raw p-value.
    Returns min(raw_p * divisor, 1.0).
    """
    return min(raw_p * BONFERRONI_DIVISOR, 1.0)

def flag_significant_pairs(
    pearson_r: float, 
    bonferroni_p: float, 
    threshold: float = BONFERRONI_THRESHOLD,
    abs_r_threshold: float = 0.5
) -> Dict[str, bool]:
    """
    Flag a correlation pair as significant based on Bonferroni-corrected p-value.
    
    Args:
        pearson_r: The Pearson correlation coefficient.
        bonferroni_p: The Bonferroni-corrected p-value.
        threshold: The significance threshold (default 0.05).
        abs_r_threshold: Optional magnitude threshold for |r| (e.g., 0.5).
    
    Returns:
        Dict with flags for 'statistically_significant' and 'strong_correlation'.
    """
    is_significant = bonferroni_p < threshold
    is_strong = abs(pearson_r) > abs_r_threshold
    
    logger.info(f"Correlation check: p={bonferroni_p:.4f} < {threshold}? {is_significant} | |r|={abs(pearson_r):.4f} > {abs_r_threshold}? {is_strong}")
    
    return {
        "statistically_significant": is_significant,
        "strong_correlation": is_strong,
        "is_both": is_significant and is_strong
    }

def run_correlation_analysis(
    df: pd.DataFrame,
    params: List[str] = None,
    indices: List[str] = None,
    lags: List[int] = None,
    output_path: str = "data/processed/correlation_results.csv"
) -> pd.DataFrame:
    """
    Run full correlation analysis across all parameter-index pairs and lags.
    Computes Neff, adjusted p-values, Bonferroni corrections, and flags significance.
    """
    if params is None:
        params = ['N_p', 'T_p', 'He2+_ratio']
    if indices is None:
        indices = ['Kp', 'Dst']
    if lags is None:
        lags = [0, 1, 2, 3, 6]
    
    results = []
    
    # Calculate global Neff for the full series (assuming df is the full series)
    # We calculate Neff for each parameter and index to be precise, or use a representative one.
    # Per spec, we use global Neff logic. We'll compute Neff for each variable involved.
    neff_cache = {}
    
    for var in params + indices:
        if var in df.columns:
            # Calculate rho1 (lag-1 autocorrelation) on detrended data
            series = df[var].dropna()
            if len(series) > 10:
                detrended = stats.signal.detrend(series)
                rho1 = np.corrcoef(detrended[:-1], detrended[1:])[0, 1]
                if np.isnan(rho1): rho1 = 0.0
                neff_cache[var] = calculate_neff(len(series), rho1)
            else:
                neff_cache[var] = len(series)
        else:
            logger.warning(f"Variable {var} not found in dataframe for Neff calculation")
    
    logger.info(f"Global Neff values calculated: {neff_cache}")
    
    for param in params:
        for index in indices:
            if param not in df.columns or index not in df.columns:
                logger.warning(f"Skipping {param} vs {index} due to missing columns")
                continue
            
            # Use the minimum Neff of the two series for conservative adjustment
            n_param = neff_cache.get(param, len(df))
            n_index = neff_cache.get(index, len(df))
            effective_n = min(n_param, n_index)
            
            # Estimate rho1 for the pair (average of the two) or use the parameter's rho1
            # Spec implies using the series properties. We'll use the average rho1 for the pair's Neff calculation if needed,
            # but the function `compute_neff_adjusted_pvalue` takes a single rho1.
            # Let's re-calculate rho1 specifically for the pair's combined effective sample logic if strictly needed,
            # but standard practice in this context often uses the lag-1 of the primary series or an average.
            # For robustness, we'll use the rho1 of the parameter series as it's the "predictor".
            series_param = df[param].dropna()
            if len(series_param) > 10:
                detrended_param = stats.signal.detrend(series_param)
                rho1_param = np.corrcoef(detrended_param[:-1], detrended_param[1:])[0, 1]
                if np.isnan(rho1_param): rho1_param = 0.0
            else:
                rho1_param = 0.0
            
            for lag in lags:
                r, rho_s, p_raw = compute_correlation_at_lag(df, param, index, lag)
                
                if np.isnan(r):
                    continue
                
                # Adjust p-value using Neff
                p_adj = compute_pvalue_with_neff(r, len(df), rho1_param) # Uses the full series length and parameter's rho1
                
                # Apply Bonferroni
                p_bonf = apply_bonferroni_correction(p_adj)
                
                # Flag significance
                flags = flag_significant_pairs(r, p_bonf)
                
                results.append({
                    "parameter": param,
                    "index": index,
                    "lag_hours": lag,
                    "pearson_r": r,
                    "spearman_rho": rho_s,
                    "p_raw": p_raw,
                    "p_neff_adjusted": p_adj,
                    "p_bonferroni": p_bonf,
                    "is_significant": flags["statistically_significant"],
                    "is_strong": flags["strong_correlation"],
                    "is_both_significant_and_strong": flags["is_both"],
                    "neff_used": effective_n
                })
    
    results_df = pd.DataFrame(results)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    results_df.to_csv(output_path, index=False)
    logger.info(f"Correlation results saved to {output_path}")
    
    return results_df