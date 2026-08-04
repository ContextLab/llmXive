import os
import json
import logging
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, Optional, Tuple, List

# Import config utilities if needed for thresholds, though T018 focuses on core stats
# from config import get_config, get_env_float

# Setup logging
logger = logging.getLogger(__name__)

def welch_t_test(df: pd.DataFrame, group_col: str, value_col: str) -> Dict[str, Any]:
    """
    Perform Welch's independent samples t-test.
    
    This is the primary statistical test for the between-subjects design
    mandated by the project plan (overriding spec FR-002).
    
    Args:
        df: Input dataframe containing the data.
        group_col: Name of the column defining the groups (e.g., 'stimulus_condition').
        value_col: Name of the column containing the metric to test (e.g., 'perseverative_errors').
        
    Returns:
        Dictionary with 'statistic', 'pvalue', 'group1_mean', 'group2_mean', 'n1', 'n2'.
        
    Raises:
        ValueError: If groups are missing or sample sizes are too small.
        RuntimeError: If variance is zero in a group.
    """
    if group_col not in df.columns or value_col not in df.columns:
        raise ValueError(f"Columns '{group_col}' or '{value_col}' not found in dataframe.")
        
    # Ensure non-null values
    clean_df = df[[group_col, value_col]].dropna()
    
    if clean_df.empty:
        raise ValueError(f"No valid data found for test on {value_col}.")
        
    groups = clean_df[group_col].unique()
    if len(groups) != 2:
        raise ValueError(f"Expected exactly 2 groups in '{group_col}', found {len(groups)}: {groups}")
        
    group1_name, group2_name = groups[0], groups[1]
    group1_data = clean_df[clean_df[group_col] == group1_name][value_col]
    group2_data = clean_df[clean_df[group_col] == group2_name][value_col]
    
    n1, n2 = len(group1_data), len(group2_data)
    
    if n1 < 10 or n2 < 10:
        logger.warning(f"Sample size too small for {value_col}: n1={n1}, n2={n2}")
        # We proceed but log, as per T023 requirements we might skip, 
        # but T018 is the implementation of the test itself. 
        # T023 handles the skipping logic in the pipeline. 
        # Here we just ensure we don't crash on empty sets.
        if n1 == 0 or n2 == 0:
            raise ValueError(f"Empty group detected for {value_col}")

    # Check for zero variance
    var1 = group1_data.var()
    var2 = group2_data.var()
    
    if var1 == 0 and var2 == 0:
        logger.error(f"Zero variance in both groups for {value_col}. Cannot compute t-test.")
        raise RuntimeError(f"Zero variance in both groups for {value_col}.")
        
    try:
        t_stat, p_val = stats.ttest_ind(group1_data, group2_data, equal_var=False)
    except Exception as e:
        logger.error(f"Error during t-test calculation for {value_col}: {e}")
        raise
        
    return {
        "test": "welch_t_test",
        "metric": value_col,
        "group1": group1_name,
        "group2": group2_name,
        "n1": int(n1),
        "n2": int(n2),
        "mean1": float(group1_data.mean()),
        "mean2": float(group2_data.mean()),
        "var1": float(var1),
        "var2": float(var2),
        "statistic": float(t_stat),
        "pvalue": float(p_val)
    }

def calculate_cohen_d(df: pd.DataFrame, group_col: str, value_col: str) -> float:
    """
    Calculate Cohen's d effect size for independent samples.
    
    Formula: (mean1 - mean2) / pooled_std
    where pooled_std = sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1 + n2 - 2))
    
    Args:
        df: Input dataframe.
        group_col: Group column name.
        value_col: Value column name.
        
    Returns:
        Cohen's d value.
    """
    clean_df = df[[group_col, value_col]].dropna()
    groups = clean_df[group_col].unique()
    
    if len(groups) != 2:
        raise ValueError("Cohen's d requires exactly 2 groups.")
        
    g1 = clean_df[clean_df[group_col] == groups[0]][value_col]
    g2 = clean_df[clean_df[group_col] == groups[1]][value_col]
    
    n1, n2 = len(g1), len(g2)
    mean1, mean2 = g1.mean(), g2.mean()
    var1, var2 = g1.var(), g2.var()
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        logger.warning(f"Pooled std is 0 for {value_col}. Returning 0 for Cohen's d.")
        return 0.0
        
    return (mean1 - mean2) / pooled_std

def calculate_effect_size_ci(df: pd.DataFrame, group_col: str, value_col: str, 
                             confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate 95% Confidence Interval for Cohen's d.
    
    Uses the non-central t-distribution approximation or standard error method.
    For simplicity and robustness in this pipeline, we use the standard error approximation:
    SE_d = sqrt((n1 + n2)/(n1*n2) + d^2/(2*(n1+n2)))
    CI = d +/- Z * SE_d
    
    Args:
        df: Input dataframe.
        group_col: Group column name.
        value_col: Value column name.
        confidence: Confidence level (default 0.95).
        
    Returns:
        Tuple (lower_bound, upper_bound).
    """
    d = calculate_cohen_d(df, group_col, value_col)
    clean_df = df[[group_col, value_col]].dropna()
    groups = clean_df[group_col].unique()
    g1 = clean_df[clean_df[group_col] == groups[0]][value_col]
    g2 = clean_df[clean_df[group_col] == groups[1]][value_col]
    n1, n2 = len(g1), len(g2)
    
    # Standard Error of d
    se_d = np.sqrt((n1 + n2) / (n1 * n2) + (d**2) / (2 * (n1 + n2)))
    
    # Z-score for confidence level
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    
    lower = d - z * se_d
    upper = d + z * se_d
    
    return float(lower), float(upper)

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction for multiple comparisons.
    
    Args:
        p_values: List of raw p-values.
        alpha: Original significance level.
        
    Returns:
        Dictionary with 'original_alpha', 'corrected_alpha', 'adjusted_p_values', 
        'significant_results' (list of indices that are significant).
    """
    n = len(p_values)
    if n == 0:
        return {
            "original_alpha": alpha,
            "corrected_alpha": alpha,
            "adjusted_p_values": [],
            "significant_results": []
        }
        
    corrected_alpha = alpha / n
    adjusted_p_values = [min(p * n, 1.0) for p in p_values]
    significant_results = [i for i, p in enumerate(adjusted_p_values) if p < corrected_alpha]
    
    return {
        "original_alpha": alpha,
        "corrected_alpha": corrected_alpha,
        "adjusted_p_values": adjusted_p_values,
        "significant_results": significant_results,
        "n_tests": n
    }

def calculate_power_and_mdes(n1: int, n2: int, effect_size: float, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Calculate statistical power and Minimum Detectable Effect Size (MDES).
    
    Args:
        n1: Sample size group 1.
        n2: Sample size group 2.
        effect_size: Observed Cohen's d.
        alpha: Significance level.
        
    Returns:
        Dictionary with 'power', 'mdes'.
    """
    # Use statsmodels for power analysis if available, otherwise fallback to scipy approximation
    # Since T002 requires statsmodels, we assume it's available.
    try:
        from statsmodels.stats.power import TTestIndPower
        
        power_analysis = TTestIndPower()
        
        # Calculate Power
        power = power_analysis.solve_power(effect_size=effect_size, 
                                           nobs1=n1, 
                                           ratio=n2/n1, 
                                           alpha=alpha, 
                                           alternative='two-sided')
        
        # Calculate MDES (Minimum Detectable Effect Size) for 80% power
        mdes = power_analysis.solve_power(effect_size=None, 
                                          nobs1=n1, 
                                          ratio=n2/n1, 
                                          alpha=alpha, 
                                          power=0.80, 
                                          alternative='two-sided')
        
        return {
            "power": float(power) if not np.isnan(power) else None,
            "mdes": float(mdes) if not np.isnan(mdes) else None,
            "target_power": 0.80,
            "alpha": alpha
        }
    except ImportError:
        # Fallback: Simple approximation or return None if statsmodels missing
        logger.warning("statsmodels not found. Skipping detailed power analysis.")
        return {
            "power": None,
            "mdes": None,
            "note": "statsmodels not available"
        }

def run_sensitivity_analysis(results: List[Dict[str, Any]], thresholds: List[float] = None) -> Dict[str, Any]:
    """
    Run sensitivity analysis by testing different significance thresholds.
    
    Args:
        results: List of test result dictionaries from welch_t_test.
        thresholds: List of alpha thresholds to test (default: [0.01, 0.05, 0.10]).
        
    Returns:
        Dictionary mapping metric names to sensitivity results.
    """
    if thresholds is None:
        thresholds = [0.01, 0.05, 0.10]
        
    sensitivity_report = {}
    
    for res in results:
        metric = res.get('metric')
        p_val = res.get('pvalue')
        
        if metric is None or p_val is None:
            continue
            
        if metric not in sensitivity_report:
            sensitivity_report[metric] = {
                "pvalue": p_val,
                "thresholds": {}
            }
            
        for t in thresholds:
            is_sig = p_val < t
            sensitivity_report[metric]["thresholds"][str(t)] = {
                "alpha": t,
                "significant": is_sig,
                "pvalue": p_val
            }
            
        # Check for borderline status (0.04 - 0.06)
        if 0.04 <= p_val <= 0.06:
            sensitivity_report[metric]["is_borderline"] = True
        else:
            sensitivity_report[metric]["is_borderline"] = False
            
    return sensitivity_report

def run_analysis(df: pd.DataFrame, metrics: List[str], group_col: str = 'stimulus_condition') -> Dict[str, Any]:
    """
    Run the full analysis pipeline for a list of metrics.
    
    Args:
        df: Cleaned dataset dataframe.
        metrics: List of column names to test (e.g., ['perseverative_errors', 'categories_completed']).
        group_col: Column name for grouping.
        
    Returns:
        Dictionary containing all test results, effect sizes, and corrections.
    """
    results = []
    effect_sizes = []
    p_values = []
    
    for metric in metrics:
        if metric not in df.columns:
            logger.warning(f"Metric {metric} not found in dataframe. Skipping.")
            continue
            
        try:
            t_res = welch_t_test(df, group_col, metric)
            d = calculate_cohen_d(df, group_col, metric)
            ci_low, ci_high = calculate_effect_size_ci(df, group_col, metric)
            
            t_res['cohens_d'] = d
            t_res['cohens_d_ci'] = [ci_low, ci_high]
            
            results.append(t_res)
            p_values.append(t_res['pvalue'])
            effect_sizes.append({
                "metric": metric,
                "d": d,
                "ci_low": ci_low,
                "ci_high": ci_high
            })
            
        except Exception as e:
            logger.error(f"Analysis failed for {metric}: {e}")
            # Continue with other metrics
            continue
            
    # Apply Bonferroni correction
    if p_values:
        correction = bonferroni_correction(p_values)
        # Map corrected p-values back to results
        for i, res in enumerate(results):
            res['pvalue_corrected'] = correction['adjusted_p_values'][i]
            res['is_significant_corrected'] = i in correction['significant_results']
    else:
        correction = {"adjusted_p_values": [], "significant_results": []}
        
    # Calculate Power and MDES for each metric
    power_results = []
    for i, res in enumerate(results):
        if i < len(effect_sizes):
            power_res = calculate_power_and_mdes(
                res['n1'], res['n2'], effect_sizes[i]['d']
            )
            power_res['metric'] = res['metric']
            power_results.append(power_res)
            
    return {
        "t_tests": results,
        "effect_sizes": effect_sizes,
        "bonferroni_correction": correction,
        "power_analysis": power_results
    }

def run_full_analysis(df: pd.DataFrame, metrics: List[str], group_col: str = 'stimulus_condition') -> Dict[str, Any]:
    """
    Orchestrates the full analysis including sensitivity checks.
    
    Args:
        df: Cleaned dataset.
        metrics: List of metrics to analyze.
        group_col: Grouping column.
        
    Returns:
        Comprehensive analysis report.
    """
    analysis_results = run_analysis(df, metrics, group_col)
    
    # Run sensitivity analysis
    if analysis_results['t_tests']:
        sensitivity = run_sensitivity_analysis(analysis_results['t_tests'])
        analysis_results['sensitivity'] = sensitivity
    else:
        analysis_results['sensitivity'] = {}
        
    return analysis_results

def main():
    """
    Entry point for running analysis on the cleaned dataset.
    Expects `data/processed/cleaned_dataset.csv` to exist.
    """
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    input_path = os.path.join("data", "processed", "cleaned_dataset.csv")
    output_path = os.path.join("data", "results", "statistical_report.json")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T014a has been completed successfully.")
        return
        
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Define metrics to analyze based on project spec
    metrics = ['perseverative_errors', 'categories_completed']
    group_col = 'stimulus_condition'
    
    # Verify group column exists
    if group_col not in df.columns:
        # Try to map common variations
        if 'stimulus_type' in df.columns:
            group_col = 'stimulus_type'
            logger.info(f"Using 'stimulus_type' as group column.")
        else:
            logger.error(f"Group column '{group_col}' (or 'stimulus_type') not found in dataset.")
            return
            
    logger.info(f"Running analysis on metrics: {metrics}")
    results = run_full_analysis(df, metrics, group_col)
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    logger.info(f"Saving results to {output_path}")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info("Analysis complete.")

if __name__ == "__main__":
    main()