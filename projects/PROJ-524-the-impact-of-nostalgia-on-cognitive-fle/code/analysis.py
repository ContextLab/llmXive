import os
import json
import logging
import numpy as np
import pandas as pd
from scipy import stats

from config import load_config, get_config, get_env_float
from utils import setup_logging, log_info, log_warning, log_error

logger = logging.getLogger(__name__)

# Constants for sensitivity analysis
DEFAULT_THRESHOLDS = [0.001, 0.01, 0.05, 0.1, 0.2]
OUTPUT_PATH = "data/results/sensitivity_report.json"

def welch_t_test(group1: pd.Series, group2: pd.Series) -> tuple:
    """
    Perform Welch's independent samples t-test.
    Returns (t_statistic, p_value).
    """
    if len(group1) < 2 or len(group2) < 2:
        raise ValueError("Both groups must have at least 2 samples for t-test.")
    return stats.ttest_ind(group1, group2, equal_var=False)

def calculate_cohen_d(group1: pd.Series, group2: pd.Series) -> float:
    """
    Calculate Cohen's d effect size for independent samples.
    Uses pooled standard deviation.
    """
    n1, n2 = len(group1), len(group2)
    mean1, mean2 = group1.mean(), group2.mean()
    var1, var2 = group1.var(ddof=1), group2.var(ddof=1)

    # Pooled standard deviation
    pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    pooled_std = np.sqrt(pooled_var)

    if pooled_std == 0:
        return 0.0

    return (mean1 - mean2) / pooled_std

def calculate_effect_size_ci(d: float, n1: int, n2: int, alpha: float = 0.05) -> tuple:
    """
    Calculate approximate 95% confidence interval for Cohen's d.
    Returns (ci_lower, ci_upper).
    """
    # Approximation using non-central t-distribution or large sample approximation
    # Using large sample approximation for simplicity:
    se_d = np.sqrt((n1 + n2) / (n1 * n2) + (d**2) / (2 * (n1 + n2)))
    z = stats.norm.ppf(1 - alpha / 2)
    ci_lower = d - z * se_d
    ci_upper = d + z * se_d
    return ci_lower, ci_upper

def bonferroni_correction(p_values: list, alpha: float = 0.05) -> list:
    """
    Apply Bonferroni correction to a list of p-values.
    Returns corrected p-values.
    """
    n = len(p_values)
    if n == 0:
        return []
    corrected = [min(p * n, 1.0) for p in p_values]
    return corrected

def calculate_power_and_mdes(t_stat: float, n1: int, n2: int, alpha: float = 0.05) -> dict:
    """
    Calculate statistical power and Minimum Detectable Effect Size (MDES).
    Returns a dict with power and mdes.
    """
    df = n1 + n2 - 2
    # Power calculation using non-central t-distribution
    # Effect size estimate from t-stat
    d_est = t_stat * np.sqrt(1/n1 + 1/n2)
    
    # Critical t-value
    t_crit = stats.t.ppf(1 - alpha/2, df)
    
    # Non-centrality parameter
    ncp = t_stat
    
    # Power = P(|T| > t_crit | H1)
    # Approximation: Power = 1 - beta
    # Using survival function
    power = 1 - (stats.t.cdf(t_crit, df, ncp) - stats.t.cdf(-t_crit, df, ncp))
    power = max(0.0, min(1.0, power))
    
    # MDES: The smallest effect size detectable with 80% power
    # Iterative approach or approximation
    # Approximation: MDES ≈ (t_alpha + t_beta) * sqrt(1/n1 + 1/n2)
    t_beta = stats.t.ppf(0.80, df) # 80% power
    mdes = (t_crit + t_beta) * np.sqrt(1/n1 + 1/n2)
    
    return {
        "power": float(power),
        "mdes": float(mdes),
        "sample_sizes": {"n1": n1, "n2": n2},
        "alpha": alpha
    }

def run_sensitivity_analysis(df: pd.DataFrame, metric_col: str, group_col: str, 
                             thresholds: list = None) -> dict:
    """
    Run sensitivity analysis by testing different significance thresholds.
    
    Args:
        df: Cleaned dataset dataframe
        metric_col: Column name for the cognitive metric (e.g., 'perseverative_errors')
        group_col: Column name for the group (e.g., 'stimulus_type')
        thresholds: List of significance thresholds to test. Defaults to DEFAULT_THRESHOLDS.
    
    Returns:
        Dictionary containing sensitivity analysis results.
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS
    
    # Ensure thresholds are floats
    thresholds = [float(t) for t in thresholds]
    
    # Sort thresholds for consistent reporting
    thresholds = sorted(thresholds)
    
    # Extract groups
    if group_col not in df.columns or metric_col not in df.columns:
        raise ValueError(f"Required columns {group_col} and {metric_col} not found in dataframe.")
    
    nostalgia_group = df[df[group_col] == 'nostalgia'][metric_col].dropna()
    control_group = df[df[group_col] == 'control'][metric_col].dropna()
    
    if len(nostalgia_group) == 0 or len(control_group) == 0:
        raise ValueError("One or both groups are empty after filtering.")
    
    # Run t-test once
    t_stat, p_val = welch_t_test(nostalgia_group, control_group)
    cohens_d = calculate_cohen_d(nostalgia_group, control_group)
    n1, n2 = len(nostalgia_group), len(control_group)
    
    # Calculate power and MDES
    power_metrics = calculate_power_and_mdes(t_stat, n1, n2)
    
    # Run sensitivity sweep
    sensitivity_results = []
    for alpha in thresholds:
        is_significant = p_val < alpha
        sensitivity_results.append({
            "threshold": alpha,
            "is_significant": is_significant,
            "p_value": p_val,
            "t_statistic": t_stat,
            "effect_size_cohen_d": cohens_d,
            "sample_sizes": {"nostalgia": n1, "control": n2}
        })
    
    # Determine stability
    significant_count = sum(1 for r in sensitivity_results if r["is_significant"])
    is_stable = significant_count == len(thresholds) or significant_count == 0
    is_borderline = any(abs(r["p_value"] - 0.05) < 0.01 for r in sensitivity_results)
    
    report = {
        "metric": metric_col,
        "comparison": "nostalgia vs control",
        "t_statistic": t_stat,
        "p_value": p_val,
        "effect_size": {
            "cohens_d": cohens_d,
            "ci_95": calculate_effect_size_ci(cohens_d, n1, n2)
        },
        "power_analysis": power_metrics,
        "sensitivity_sweep": sensitivity_results,
        "summary": {
            "is_stable_across_thresholds": is_stable,
            "is_borderline": is_borderline,
            "significant_at_count": significant_count,
            "total_thresholds_tested": len(thresholds),
            "thresholds_tested": thresholds
        }
    }
    
    return report

def run_analysis(df: pd.DataFrame, config: dict = None) -> dict:
    """
    Run standard analysis (Welch's t-test, effect sizes, power).
    """
    if config is None:
        config = get_config()
    
    metric_col = config.get("primary_metric", "perseverative_errors")
    group_col = config.get("group_column", "stimulus_type")
    
    return run_sensitivity_analysis(df, metric_col, group_col, thresholds=[0.05])

def run_full_analysis(df: pd.DataFrame, output_path: str = None) -> dict:
    """
    Run full analysis including sensitivity sweep and save results.
    """
    if output_path is None:
        output_path = OUTPUT_PATH
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Run sensitivity analysis with default thresholds
    result = run_sensitivity_analysis(df)
    
    # Save to JSON
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    log_info(f"Sensitivity analysis report saved to {output_path}")
    return result

def main():
    """
    Main entry point for running sensitivity analysis.
    """
    setup_logging(level=logging.INFO)
    
    config = load_config()
    data_path = config.get("data_paths", {}).get("cleaned_dataset", "data/processed/cleaned_dataset.csv")
    
    if not os.path.exists(data_path):
        log_error(f"Cleaned dataset not found at {data_path}")
        return
    
    log_info(f"Loading dataset from {data_path}")
    df = pd.read_csv(data_path)
    
    log_info("Running sensitivity analysis...")
    result = run_full_analysis(df)
    
    log_info("Analysis complete.")
    log_info(f"Summary: Stable={result['summary']['is_stable_across_thresholds']}, "
             f"Borderline={result['summary']['is_borderline']}")

if __name__ == "__main__":
    main()