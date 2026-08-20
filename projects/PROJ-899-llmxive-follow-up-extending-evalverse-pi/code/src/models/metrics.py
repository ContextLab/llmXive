import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from scipy import stats
import pandas as pd
import os
from src.utils import get_logger, write_csv, ensure_directories
from src.config import get_data_root

logger = get_logger(__name__)

def pearson_correlation(x: np.ndarray, y: np.ndarray) -> float:
    """Calculate Pearson correlation coefficient."""
    if len(x) != len(y):
        raise ValueError("Arrays must have the same length")
    if len(x) < 2:
        return 0.0
    return stats.pearsonr(x, y)[0]

def spearman_correlation(x: np.ndarray, y: np.ndarray) -> float:
    """Calculate Spearman rank correlation coefficient."""
    if len(x) != len(y):
        raise ValueError("Arrays must have the same length")
    if len(x) < 2:
        return 0.0
    return stats.spearmanr(x, y)[0]

def bootstrap_confidence_interval(
    x: np.ndarray, 
    y: np.ndarray, 
    n_bootstraps: int = 1000, 
    alpha: float = 0.05
) -> Tuple[float, float]:
    """
    Calculate 95% Confidence Interval for correlation using bootstrapping.
    Returns (lower_bound, upper_bound).
    """
    n = len(x)
    correlations = []
    rng = np.random.default_rng(42) # Fixed seed for reproducibility

    for _ in range(n_bootstraps):
        idx = rng.choice(n, size=n, replace=True)
        corr = stats.pearsonr(x[idx], y[idx])[0]
        correlations.append(corr)

    correlations = np.array(correlations)
    lower = np.percentile(correlations, 100 * alpha / 2)
    upper = np.percentile(correlations, 100 * (1 - alpha / 2))
    
    return float(lower), float(upper)

def run_permutation_test(
    x: np.ndarray, 
    y: np.ndarray, 
    n_permutations: int = 1000
) -> Dict[str, Any]:
    """
    Run permutation test for multiple comparison correction.
    Returns p-value and observed statistic.
    """
    n = len(x)
    observed_corr = stats.pearsonr(x, y)[0]
    rng = np.random.default_rng(42)
    
    count_extreme = 0
    for _ in range(n_permutations):
        perm_y = rng.permutation(y)
        perm_corr = stats.pearsonr(x, perm_y)[0]
        if abs(perm_corr) >= abs(observed_corr):
            count_extreme += 1

    p_value = count_extreme / n_permutations
    
    return {
        "observed_statistic": float(observed_corr),
        "p_value": float(p_value),
        "n_permutations": n_permutations
    }

def calculate_dimension_metrics(
    features: np.ndarray, 
    scores: np.ndarray, 
    dimension_name: str
) -> Dict[str, Any]:
    """
    Calculate all metrics for a single dimension.
    """
    # Flatten if needed
    if features.ndim > 1:
        # Assuming features are already aggregated per sample for this dimension
        pass 
    
    p_corr = pearson_correlation(features.flatten(), scores)
    s_corr = spearman_correlation(features.flatten(), scores)
    lower_ci, upper_ci = bootstrap_confidence_interval(features.flatten(), scores)
    perm_result = run_permutation_test(features.flatten(), scores)

    return {
        "dimension": dimension_name,
        "pearson": float(p_corr),
        "spearman": float(s_corr),
        "ci_lower": float(lower_ci),
        "ci_upper": float(upper_ci),
        "p_value": float(perm_result["p_value"])
    }

def run_threshold_sweep(
    dimension_results: pd.DataFrame, 
    thresholds: List[float] = [0.80, 0.85, 0.90]
) -> pd.DataFrame:
    """
    T026 Implementation: Run threshold sweep logic.
    Reads dimension metrics and classifies status at each threshold.
    
    Output: DataFrame with columns [dimension, threshold, status]
    Writes to: data/sensitivity_sweep_raw.csv
    """
    if dimension_results.empty:
        logger.warning("No dimension results to sweep.")
        return pd.DataFrame(columns=['dimension', 'threshold', 'status'])

    results = []
    
    # Ensure we have the correlation column
    corr_col = 'pearson' if 'pearson' in dimension_results.columns else 'spearman'
    
    for _, row in dimension_results.iterrows():
        dim_name = row['dimension']
        r_val = row[corr_col]
        
        for thresh in thresholds:
            # Classification logic based on T017/US3 spec
            # "feature-sufficient" if r >= 0.85 (or current threshold)
            # "VLM-required" if lower CI < 0.70 (simplified for sweep: just check r vs thresh)
            # For the sweep, we simply check if the correlation meets the threshold
            if r_val >= thresh:
                status = "feature-sufficient"
            else:
                status = "VLM-required"
            
            results.append({
                "dimension": dim_name,
                "threshold": thresh,
                "status": status
            })

    sweep_df = pd.DataFrame(results)
    
    # Write to disk as per T026 requirement
    data_root = get_data_root()
    ensure_directories()
    output_path = os.path.join(data_root, "sensitivity_sweep_raw.csv")
    sweep_df.to_csv(output_path, index=False)
    logger.info(f"Wrote sensitivity sweep raw data to {output_path}")
    
    return sweep_df

def apply_fwer_correction(p_values: List[float], alpha: float = 0.05) -> List[bool]:
    """
    Apply Bonferroni correction for Family-Wise Error Rate.
    Returns list of booleans indicating significance.
    """
    n = len(p_values)
    if n == 0:
        return []
    adjusted_alpha = alpha / n
    return [p < adjusted_alpha for p in p_values]

def main():
    """
    Main entry point for metrics module if run directly.
    """
    logger.info("Metrics module loaded. Use specific functions.")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
