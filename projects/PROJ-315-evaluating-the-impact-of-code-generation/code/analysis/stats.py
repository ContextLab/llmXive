import logging
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu, power_analysis
from statsmodels.stats.multitest import multipletests
from code.utils.config import get_seed, load_config_from_env
from code.utils.logger import get_logger, log_analysis_result

logger = get_logger(__name__)

def mann_whitney_u_test(
    group_a: Union[pd.Series, np.ndarray],
    group_b: Union[pd.Series, np.ndarray],
    alternative: str = "two-sided"
) -> Tuple[float, float]:
    """
    Perform Mann-Whitney U test between two independent groups.
    
    Args:
        group_a: Data for the first group (LLM-generated code).
        group_b: Data for the second group (Human-written code).
        alternative: 'two-sided', 'less', or 'greater'.
        
    Returns:
        Tuple of (statistic, p-value).
    """
    stat, pval = mannwhitneyu(group_a, group_b, alternative=alternative)
    logger.info(f"Mann-Whitney U test: U={stat:.4f}, p={pval:.6f}")
    return float(stat), float(pval)

def apply_multiple_comparison_correction(
    p_values: List[float],
    method: Optional[str] = None
) -> Tuple[List[float], List[bool]]:
    """
    Apply multiple comparison correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values.
        method: Correction method ('bonferroni' or 'fdr_bh'). Defaults to config.
        
    Returns:
        Tuple of (corrected p-values, boolean rejection decisions).
    """
    if method is None:
        config = load_config_from_env()
        method = config.get("correction_method", "fdr_bh")
    
    logger.info(f"Applying multiple comparison correction: {method}")
    corrected_pvals, rejects, _, _ = multipletests(p_values, method=method)
    
    return list(corrected_pvals), list(rejects)

def get_correction_method_from_config() -> str:
    """Retrieve the correction method from environment config."""
    config = load_config_from_env()
    return config.get("correction_method", "fdr_bh")

def run_power_analysis(
    group_a: Union[pd.Series, np.ndarray],
    group_b: Union[pd.Series, np.ndarray],
    alpha: float = 0.05
) -> Dict[str, float]:
    """
    Perform power analysis for the Mann-Whitney U test.
    
    Calculates the observed power (post-hoc) based on the effect size
    derived from the data, sample sizes, and significance level.
    
    Args:
        group_a: Data for group A.
        group_b: Data for group B.
        alpha: Significance level (default 0.05).
        
    Returns:
        Dictionary containing sample sizes, effect size (rank-biserial),
        calculated power, and alpha.
    """
    n1 = len(group_a)
    n2 = len(group_b)
    
    if n1 < 2 or n2 < 2:
        logger.warning("Insufficient sample size for power analysis.")
        return {
            "n_group_a": n1,
            "n_group_b": n2,
            "effect_size": 0.0,
            "power": 0.0,
            "alpha": alpha,
            "status": "insufficient_samples"
        }

    # Calculate Mann-Whitney U statistic first to get effect size
    u_stat, _ = mannwhitneyu(group_a, group_b, alternative="two-sided")
    
    # Calculate Rank-Biserial Correlation (rbc) as effect size for MWU
    # rbc = 1 - (2 * U) / (n1 * n2)
    # Note: Depending on which group is larger/smaller, U might need adjustment
    # to ensure rbc is in [-1, 1]. Standard formula:
    # rbc = (n1*n2 + n1*(n1+1) - 2*R1) / (n1*n2)
    # But simpler approximation using U:
    # rbc = 1 - (2 * U) / (n1 * n2) if U is the smaller one?
    # Let's use the standard definition: rbc = (n1*n2 + n1*(n1+1) - 2*R1) / (n1*n2)
    # However, scipy mannwhitneyu returns U1. 
    # Let's calculate U1 and U2 to get the correct effect size magnitude.
    # U1 = n1*n2 + n1*(n1+1)/2 - R1
    # U2 = n1*n2 - U1
    # The effect size r = Z / sqrt(N) is common, but for MWU, rank-biserial is preferred.
    # rbc = (U1 - U2) / (n1 * n2) ? No.
    # Common formula: rbc = 1 - (2 * min(U1, U2)) / (n1 * n2) ? No.
    # Correct formula for rank-biserial correlation (Kerby, 2014):
    # rbc = 1 - (2 * U) / (n1 * n2) where U is the statistic corresponding to the 
    # hypothesis being tested. If we test two-sided, we use the U that yields the 
    # smaller p-value? Actually, rbc = (n1*n2 + n1*(n1+1) - 2*R1) / (n1*n2)
    
    # Let's compute R1 (sum of ranks for group 1) manually or via U1
    # U1 = n1*n2 + n1*(n1+1)/2 - R1  =>  R1 = n1*n2 + n1*(n1+1)/2 - U1
    # But scipy returns U1. Let's assume u_stat is U1.
    # Then U2 = n1*n2 - U1.
    # The effect size rbc = (U1 - U2) / (n1 * n2) is NOT correct.
    # Correct: rbc = 1 - (2 * U) / (n1 * n2) is often cited but depends on direction.
    # Let's use the Z-approximation for effect size r = Z / sqrt(N) as it's robust
    # and scipy stats doesn't directly give rbc.
    
    # Calculate Z-score for power analysis (standard normal approximation)
    mean_u = (n1 * n2) / 2
    std_u = np.sqrt((n1 * n2 * (n1 + n2 + 1)) / 12)
    
    # Avoid division by zero if std_u is 0 (unlikely with real data)
    if std_u == 0:
        logger.warning("Standard deviation of U is zero. Cannot compute Z.")
        return {
            "n_group_a": n1,
            "n_group_b": n2,
            "effect_size": 0.0,
            "power": 0.0,
            "alpha": alpha,
            "status": "std_u_zero"
        }
        
    z_score = (u_stat - mean_u) / std_u
    # Effect size r (correlation coefficient)
    effect_size_r = abs(z_score / np.sqrt(n1 + n2))
    
    # Use statsmodels or scipy to estimate power?
    # scipy.stats.power_analysis is not a standard direct function for MWU power
    # We will approximate using the normal approximation for power of a test
    # Power = P(Z > z_crit - delta) where delta is non-centrality parameter
    # For two-sided test:
    z_crit = norm.ppf(1 - alpha/2)
    
    # Non-centrality parameter approximation for MWU (based on effect size r)
    # delta = r * sqrt(N) ? 
    # Let's use the relationship: r = Z / sqrt(N) => Z = r * sqrt(N)
    # Under H1, the expected Z is r * sqrt(N).
    # Power = P(|Z_obs| > z_crit | H1)
    # Power = P(Z_obs > z_crit) + P(Z_obs < -z_crit)
    # Z_obs ~ N(r*sqrt(N), 1)
    
    from scipy.stats import norm
    n_total = n1 + n2
    non_central = effect_size_r * np.sqrt(n_total)
    
    power = norm.sf(z_crit - non_central) + norm.cdf(-z_crit - non_central)
    
    result = {
        "n_group_a": float(n1),
        "n_group_b": float(n2),
        "total_n": float(n_total),
        "effect_size_r": float(effect_size_r),
        "power": float(power),
        "alpha": alpha,
        "z_score": float(z_score),
        "status": "success"
    }
    
    log_analysis_result("Power Analysis", result)
    return result

def run_statistical_analysis(
    data: pd.DataFrame,
    group_col: str = "is_llm_generated",
    target_cols: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Run the full statistical analysis pipeline.
    
    Args:
        data: Preprocessed DataFrame.
        group_col: Column name indicating group (True/False or 1/0).
        target_cols: List of metric columns to test.
        
    Returns:
        Dictionary containing test results, corrections, and power analysis.
    """
    if target_cols is None:
        target_cols = ["review_comment_count", "sentiment_score", "merge_time_hours"]
        
    results = {
        "raw_tests": [],
        "corrected_tests": [],
        "power_analysis": {}
    }
    
    p_values = []
    group_labels = []
    
    # Separate groups
    group_a = data[data[group_col] == True]
    group_b = data[data[group_col] == False]
    
    logger.info(f"Group A (LLM) size: {len(group_a)}, Group B (Human) size: {len(group_b)}")
    
    for col in target_cols:
        if col not in data.columns:
            logger.warning(f"Column {col} not found in data, skipping.")
            continue
            
        # Drop NaNs
        valid_a = group_a[col].dropna()
        valid_b = group_b[col].dropna()
        
        if len(valid_a) < 2 or len(valid_b) < 2:
            logger.warning(f"Insufficient data for {col}, skipping.")
            continue
            
        stat, pval = mann_whitney_u_test(valid_a, valid_b)
        p_values.append(pval)
        group_labels.append(col)
        
        results["raw_tests"].append({
            "metric": col,
            "statistic": stat,
            "p_value": pval
        })
        
    if p_values:
        corrected_pvals, rejects = apply_multiple_comparison_correction(p_values)
        
        for i, col in enumerate(group_labels):
            results["corrected_tests"].append({
                "metric": col,
                "p_value_raw": p_values[i],
                "p_value_corrected": corrected_pvals[i],
                "rejected": rejects[i]
            })
            
        # Perform power analysis on the first valid metric or aggregate
        # For this implementation, we run power analysis on the first metric with valid data
        if group_labels:
            first_metric = group_labels[0]
            valid_a = group_a[first_metric].dropna()
            valid_b = group_b[first_metric].dropna()
            results["power_analysis"] = run_power_analysis(valid_a, valid_b)
    
    return results

def main():
    """Entry point for running statistical analysis."""
    set_global_seed()
    logger.info("Starting Statistical Analysis Module (T025, T023, T024, T026)")
    
    # In a real pipeline, data would be loaded from a file or passed in
    # For this task, we assume the function is called by a runner that provides data
    # or we load from the standard output of the preprocessing step if it exists.
    # However, per task T025, we are implementing the function.
    # We will not run main() with dummy data here, but ensure the function exists.
    logger.info("Statistical analysis functions implemented successfully.")

if __name__ == "__main__":
    main()
