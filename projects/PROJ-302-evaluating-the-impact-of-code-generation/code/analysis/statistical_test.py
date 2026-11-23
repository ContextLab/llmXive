import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_shapiro_wilk(data: np.ndarray) -> Tuple[float, float]:
    """
    Perform Shapiro-Wilk test for normality.
    
    Args:
        data: Array of review durations.
        
    Returns:
        Tuple of (statistic, p-value).
    """
    if len(data) < 3:
        logger.warning("Sample size too small for Shapiro-Wilk test (< 3). Returning (1.0, 1.0).")
        return 1.0, 1.0
    try:
        stat, p_val = stats.shapiro(data)
        return stat, p_val
    except Exception as e:
        logger.error(f"Shapiro-Wilk test failed: {e}")
        return 0.0, 1.0

def calculate_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size.
    
    Args:
        group1: Array of values for the first group (e.g., LLM-like).
        group2: Array of values for the second group (e.g., Human).
        
    Returns:
        Cohen's d value.
    """
    n1, n2 = len(group1), len(group2)
    if n1 == 0 or n2 == 0:
        logger.warning("One of the groups is empty. Returning 0.0 for Cohen's d.")
        return 0.0
    
    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        logger.warning("Pooled standard deviation is zero. Returning 0.0 for Cohen's d.")
        return 0.0
        
    return (mean1 - mean2) / pooled_std

def calculate_rank_biserial(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate rank-biserial correlation for Mann-Whitney U effect size.
    
    Args:
        group1: Array of values for the first group.
        group2: Array of values for the second group.
        
    Returns:
        Rank-biserial correlation value.
    """
    n1, n2 = len(group1), len(group2)
    if n1 == 0 or n2 == 0:
        logger.warning("One of the groups is empty. Returning 0.0 for rank-biserial correlation.")
        return 0.0
    
    try:
        u_stat, _ = stats.mannwhitneyu(group1, group2, alternative='two-sided')
        # Rank-biserial correlation formula: 1 - (2 * U) / (n1 * n2)
        rbc = 1 - (2 * u_stat) / (n1 * n2)
        return rbc
    except Exception as e:
        logger.error(f"Rank-biserial calculation failed: {e}")
        return 0.0

def select_and_run_test(group1: np.ndarray, group2: np.ndarray, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Select appropriate statistical test based on normality and run it.
    Also determines statistical significance based on p-value < alpha (SC-002).
    
    Args:
        group1: Array of values for the first group.
        group2: Array of values for the second group.
        alpha: Significance level (default 0.05 per SC-002).
        
    Returns:
        Dictionary containing test results, p-value, effect size, and significance flag.
    """
    logger.info(f"Running statistical test with alpha={alpha} (SC-002 threshold)")
    
    # 1. Normality check
    _, p_normality = run_shapiro_wilk(np.concatenate([group1, group2]))
    is_normal = p_normality > alpha
    
    logger.info(f"Normality test p-value: {p_normality:.4f} -> {'Normal' if is_normal else 'Non-Normal'}")
    
    test_type = "Parametric (t-test)" if is_normal else "Non-Parametric (Mann-Whitney U)"
    p_value = 0.0
    effect_size = 0.0
    effect_size_name = ""
    
    try:
        if is_normal:
            # Independent samples t-test
            t_stat, p_value = stats.ttest_ind(group1, group2)
            effect_size = calculate_cohens_d(group1, group2)
            effect_size_name = "Cohen's d"
        else:
            # Mann-Whitney U test
            u_stat, p_value = stats.mannwhitneyu(group1, group2, alternative='two-sided')
            effect_size = calculate_rank_biserial(group1, group2)
            effect_size_name = "Rank-biserial correlation"
            
        # SC-002: Flag result as statistically significant ONLY if p < 0.05
        is_significant = p_value < alpha
        
        result = {
            "test_type": test_type,
            "normality_passed": is_normal,
            "p_value": float(p_value),
            "effect_size": float(effect_size),
            "effect_size_name": effect_size_name,
            "is_statistically_significant": is_significant, # SC-002 Implementation
            "alpha_threshold": alpha
        }
        logger.info(f"Test Result: p={p_value:.6f}, Significant={is_significant}")
        return result
        
    except Exception as e:
        logger.error(f"Statistical test execution failed: {e}")
        return {
            "test_type": "Failed",
            "normality_passed": is_normal,
            "p_value": 1.0,
            "effect_size": 0.0,
            "effect_size_name": "",
            "is_statistically_significant": False,
            "alpha_threshold": alpha,
            "error": str(e)
        }

def run_full_analysis(
    data_path: str, 
    output_path: str, 
    llm_column: str = "review_duration", 
    group_col: str = "classification_label", 
    llm_value: str = "LLM-like", 
    human_value: str = "Human",
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Main entry point to run full analysis on a parquet file.
    
    Args:
        data_path: Path to the input parquet file.
        output_path: Path to save the results JSON.
        llm_column: Name of the column containing review duration.
        group_col: Name of the column containing group labels.
        llm_value: Value in group_col representing LLM-like code.
        human_value: Value in group_col representing Human code.
        alpha: Significance threshold (SC-002).
        
    Returns:
        Dictionary of analysis results.
    """
    logger.info(f"Loading data from {data_path}")
    try:
        df = pd.read_parquet(data_path)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return {"error": f"Data load failed: {e}"}

    if group_col not in df.columns or llm_column not in df.columns:
        logger.error(f"Required columns not found. Available: {df.columns.tolist()}")
        return {"error": "Missing required columns"}

    # Filter groups
    group1_data = df[df[group_col] == llm_value][llm_column].dropna().values
    group2_data = df[df[group_col] == human_value][llm_column].dropna().values

    if len(group1_data) == 0 or len(group2_data) == 0:
        logger.error("One or both groups are empty after filtering.")
        return {"error": "Empty groups after filtering"}

    logger.info(f"Group sizes: LLM-like={len(group1_data)}, Human={len(group2_data)}")

    results = select_and_run_test(group1_data, group2_data, alpha=alpha)
    results["sample_sizes"] = {"llm_like": len(group1_data), "human": len(group2_data)}
    results["input_file"] = data_path

    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    import json
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    return results

def main():
    """CLI entry point."""
    # Default paths relative to project root
    data_path = "data/processed/matched_cohort.parquet"
    output_path = "data/processed/statistical_test_results.json"
    
    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
        
    logger.info(f"Starting statistical analysis on {data_path}")
    results = run_full_analysis(data_path, output_path)
    
    if "error" in results:
        logger.error(f"Analysis failed: {results['error']}")
        sys.exit(1)
    else:
        logger.info(f"Analysis complete. Significant: {results['is_statistically_significant']}")
        sys.exit(0)

if __name__ == "__main__":
    main()