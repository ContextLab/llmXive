import os
import json
import logging
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.power import TTestIndPower
from pathlib import Path

# Configure logging for the module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def welch_t_test(group1: pd.Series, group2: pd.Series, metric_name: str) -> dict:
    """
    Perform Welch's independent samples t-test.
    
    Args:
        group1: Series of values for group 1 (e.g., nostalgia).
        group2: Series of values for group 2 (e.g., control).
        metric_name: Name of the metric being tested (for logging).
        
    Returns:
        Dictionary with test results or error status.
    """
    n1 = len(group1)
    n2 = len(group2)
    
    # Error Handling: Sample size too small (< 10 per group)
    if n1 < 10 or n2 < 10:
        logger.error(f"ERR_SMALL_SAMPLE: {metric_name} - Group 1 size: {n1}, Group 2 size: {n2}. Minimum required: 10. Skipping test.")
        return {
            "metric": metric_name,
            "status": "skipped",
            "reason": "ERR_SMALL_SAMPLE",
            "n1": n1,
            "n2": n2
        }

    # Error Handling: Zero Variance
    var1 = group1.var()
    var2 = group2.var()
    
    if var1 == 0 and var2 == 0:
        logger.error(f"ERR_ZERO_VARIANCE: {metric_name} - Both groups have zero variance. Cannot compute t-test.")
        return {
            "metric": metric_name,
            "status": "skipped",
            "reason": "ERR_ZERO_VARIANCE",
            "var1": var1,
            "var2": var2
        }
    
    # If one group has zero variance but the other doesn't, scipy will handle it, 
    # but we log a warning as it might indicate a data issue.
    if var1 == 0 or var2 == 0:
        logger.warning(f"WARN_ZERO_VARIANCE: {metric_name} - One group has zero variance. Proceeding with caution.")

    try:
        t_stat, p_value = stats.ttest_ind(group1, group2, equal_var=False)
        return {
            "metric": metric_name,
            "status": "success",
            "t_statistic": float(t_stat),
            "p_value": float(p_value),
            "n1": n1,
            "n2": n2
        }
    except Exception as e:
        logger.error(f"ERR_TEST_FAILURE: {metric_name} - {str(e)}")
        return {
            "metric": metric_name,
            "status": "failed",
            "reason": str(e)
        }

def calculate_cohen_d(group1: pd.Series, group2: pd.Series, metric_name: str) -> dict:
    """
    Calculate Cohen's d effect size.
    """
    n1 = len(group1)
    n2 = len(group2)
    
    if n1 < 2 or n2 < 2:
        logger.error(f"ERR_SMALL_SAMPLE: {metric_name} - Insufficient sample size for effect size calculation.")
        return {"metric": metric_name, "status": "skipped", "reason": "ERR_SMALL_SAMPLE"}

    mean1, mean2 = group1.mean(), group2.mean()
    std1, std2 = group1.std(ddof=1), group2.std(ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        logger.warning(f"WARN_ZERO_VARIANCE: {metric_name} - Pooled std dev is 0. Cohen's d undefined.")
        return {"metric": metric_name, "status": "skipped", "reason": "ERR_ZERO_VARIANCE"}
        
    d = (mean1 - mean2) / pooled_std
    
    return {
        "metric": metric_name,
        "status": "success",
        "cohens_d": float(d),
        "mean1": float(mean1),
        "mean2": float(mean2),
        "pooled_std": float(pooled_std)
    }

def calculate_effect_size_ci(d: float, n1: int, n2: int, confidence: float = 0.95) -> dict:
    """
    Calculate 95% Confidence Interval for Cohen's d.
    Uses approximation based on non-central t-distribution logic or simple SE approximation.
    Here using standard error approximation for CI.
    """
    se_d = np.sqrt((n1 + n2) / (n1 * n2) + (d**2) / (2 * (n1 + n2)))
    z = stats.norm.ppf((1 + confidence) / 2)
    ci_lower = d - z * se_d
    ci_upper = d + z * se_d
    
    return {
        "cohens_d": d,
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper),
        "confidence": confidence
    }

def bonferroni_correction(p_values: list, num_comparisons: int) -> list:
    """
    Apply Bonferroni correction to a list of p-values.
    """
    corrected = [min(p * num_comparisons, 1.0) for p in p_values]
    return corrected

def calculate_power_and_mdes(effect_size: float, n1: int, n2: int, alpha: float = 0.05) -> dict:
    """
    Calculate statistical power and Minimum Detectable Effect Size (MDES).
    """
    power_analysis = TTestIndPower()
    
    # Calculate Power
    try:
        power = power_analysis.solve_power(effect_size=effect_size, nobs1=n1, alpha=alpha, ratio=n2/n1)
    except Exception:
        power = 0.0
        
    # Calculate MDES for 80% power
    try:
        mdes = power_analysis.solve_power(power=0.80, nobs1=n1, alpha=alpha, ratio=n2/n1)
    except Exception:
        mdes = None
        
    return {
        "observed_power": float(power) if power is not None else None,
        "mdes": float(mdes) if mdes is not None else None,
        "alpha": alpha,
        "target_power": 0.80
    }

def run_sensitivity_analysis(p_value: float, thresholds: list = [0.04, 0.05, 0.06, 0.10]) -> dict:
    """
    Run sensitivity analysis by checking significance across different thresholds.
    """
    results = {}
    is_sensitive = False
    
    # Check borderline range 0.04 <= p <= 0.06
    if 0.04 <= p_value <= 0.06:
        is_sensitive = True
        
    for t in thresholds:
        results[t] = p_value < t
        
    return {
        "p_value": p_value,
        "thresholds": results,
        "is_sensitive_to_threshold": is_sensitive
    }

def run_analysis(df: pd.DataFrame, metrics: list, alpha: float = 0.05) -> dict:
    """
    Run the full analysis pipeline on the provided dataframe.
    """
    if 'stimulus_type' not in df.columns:
        raise ValueError("DataFrame must contain 'stimulus_type' column")
        
    results = {
        "t_tests": [],
        "effect_sizes": [],
        "power_analysis": [],
        "correction": {}
    }
    
    p_values = []
    
    for metric in metrics:
        if metric not in df.columns:
            logger.warning(f"Metric {metric} not found in dataframe. Skipping.")
            continue
            
        group_nostalgia = df[df['stimulus_type'] == 'nostalgia'][metric]
        group_control = df[df['stimulus_type'] == 'control'][metric]
        
        # Run T-Test
        t_result = welch_t_test(group_nostalgia, group_control, metric)
        results["t_tests"].append(t_result)
        
        if t_result["status"] == "success":
            p_values.append(t_result["p_value"])
            
            # Run Effect Size
            d_result = calculate_cohen_d(group_nostalgia, group_control, metric)
            if d_result["status"] == "success":
                ci_result = calculate_effect_size_ci(d_result["cohens_d"], len(group_nostalgia), len(group_control))
                d_result["ci"] = ci_result
                results["effect_sizes"].append(d_result)
                
                # Run Power Analysis
                power_result = calculate_power_and_mdes(d_result["cohens_d"], len(group_nostalgia), len(group_control))
                results["power_analysis"].append(power_result)
                
    # Bonferroni Correction
    if p_values:
        corrected_p = bonferroni_correction(p_values, len(p_values))
        results["correction"] = {
            "method": "bonferroni",
            "num_comparisons": len(p_values),
            "original_p_values": p_values,
            "corrected_p_values": corrected_p
        }
        
    return results

def run_full_analysis(input_path: str, output_path: str) -> None:
    """
    Load data, run analysis, and save results to JSON.
    """
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    metrics = ['perseverative_errors', 'categories_completed']
    analysis_results = run_analysis(df, metrics)
    
    logger.info(f"Saving results to {output_path}")
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(analysis_results, f, indent=2)
        
    logger.info("Analysis complete.")

def main():
    # Default paths can be overridden by environment or command line args in a real runner
    input_file = "data/processed/cleaned_dataset.csv"
    output_file = "data/results/statistical_report.json"
    
    if os.path.exists(input_file):
        run_full_analysis(input_file, output_file)
    else:
        logger.error(f"Input file {input_file} not found. Cannot run analysis.")
        raise FileNotFoundError(f"Input file {input_file} not found")

if __name__ == "__main__":
    main()