import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats
import pandas as pd

from utils.config import get_config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_shapiro_wilk(data: List[float]) -> Tuple[float, float]:
    """
    Perform Shapiro-Wilk test for normality.
    
    Args:
        data: List of numerical values.
        
    Returns:
        Tuple of (statistic, p-value).
    """
    if len(data) < 3:
        logger.warning("Not enough data points for Shapiro-Wilk test (< 3). Returning (0.0, 1.0).")
        return 0.0, 1.0
    
    try:
        stat, p_val = stats.shapiro(data)
        return stat, p_val
    except Exception as e:
        logger.error(f"Shapiro-Wilk test failed: {e}")
        return 0.0, 1.0

def calculate_cohens_d(group1: List[float], group2: List[float]) -> float:
    """
    Calculate Cohen's d effect size.
    
    Args:
        group1: List of values for group 1.
        group2: List of values for group 2.
        
    Returns:
        Cohen's d value.
    """
    n1, n2 = len(group1), len(group2)
    if n1 == 0 or n2 == 0:
        logger.error("Cannot calculate Cohen's d with empty groups.")
        return 0.0
    
    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    if var1 == 0 and var2 == 0:
        return 0.0
    
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
        
    return (mean1 - mean2) / pooled_std

def calculate_rank_biserial(group1: List[float], group2: List[float]) -> float:
    """
    Calculate rank-biserial correlation (effect size for Mann-Whitney U).
    
    Args:
        group1: List of values for group 1.
        group2: List of values for group 2.
        
    Returns:
        Rank-biserial correlation coefficient.
    """
    n1, n2 = len(group1), len(group2)
    if n1 == 0 or n2 == 0:
        return 0.0
    
    # Perform Mann-Whitney U test to get U statistic
    try:
        u_stat, _ = stats.mannwhitneyu(group1, group2, alternative='two-sided')
        # Rank-biserial r = 1 - (2 * U) / (n1 * n2)
        # Note: This formula assumes U is the smaller of the two U statistics.
        # scipy returns the statistic for the first group vs second.
        # The correlation r = (U / (n1 * n2)) - 0.5 is another form, but 1 - 2U/(n1n2) is standard for r_rb.
        # Let's use the standard definition: r_rb = 1 - (2 * min(U1, U2)) / (n1 * n2)
        
        # Calculate U2 = n1*n2 - U1
        u_stat_2 = n1 * n2 - u_stat
        min_u = min(u_stat, u_stat_2)
        
        if n1 * n2 == 0:
            return 0.0
            
        r_rb = 1 - (2 * min_u) / (n1 * n2)
        return r_rb
    except Exception as e:
        logger.error(f"Rank-biserial calculation failed: {e}")
        return 0.0

def select_and_run_test(group1: List[float], group2: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Select appropriate statistical test based on normality and run it.
    Returns p-value, effect size, and test type.
    
    Args:
        group1: List of values for group 1.
        group2: List of values for group 2.
        alpha: Significance level for normality test.
        
    Returns:
        Dictionary with test results.
    """
    if len(group1) < 3 or len(group2) < 3:
        logger.warning("Insufficient data for statistical testing. Returning default results.")
        return {
            "test_type": "none",
            "p_value": 1.0,
            "effect_size": 0.0,
            "effect_size_type": "none",
            "is_significant": False,
            "message": "Insufficient data"
        }

    # Check normality for both groups
    _, p_norm1 = run_shapiro_wilk(group1)
    _, p_norm2 = run_shapiro_wilk(group2)
    
    is_normal = (p_norm1 > alpha) and (p_norm2 > alpha)
    
    result = {
        "test_type": "none",
        "p_value": 1.0,
        "effect_size": 0.0,
        "effect_size_type": "none",
        "is_significant": False,
        "normality": {
            "group1_p": p_norm1,
            "group2_p": p_norm2,
            "both_normal": is_normal
        }
    }
    
    if is_normal:
        # Perform Independent Samples T-Test
        try:
            t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=True) # Assuming equal variance for simplicity
            result["test_type"] = "t-test"
            result["p_value"] = float(p_val)
            result["effect_size"] = float(calculate_cohens_d(group1, group2))
            result["effect_size_type"] = "Cohen's d"
        except Exception as e:
            logger.error(f"T-test failed: {e}")
            # Fallback to Mann-Whitney if t-test fails
            u_stat, p_val = stats.mannwhitneyu(group1, group2, alternative='two-sided')
            result["test_type"] = "mann-whitney (fallback)"
            result["p_value"] = float(p_val)
            result["effect_size"] = float(calculate_rank_biserial(group1, group2))
            result["effect_size_type"] = "Rank-biserial"
    else:
        # Perform Mann-Whitney U Test
        try:
            u_stat, p_val = stats.mannwhitneyu(group1, group2, alternative='two-sided')
            result["test_type"] = "mann-whitney u"
            result["p_value"] = float(p_val)
            result["effect_size"] = float(calculate_rank_biserial(group1, group2))
            result["effect_size_type"] = "Rank-biserial"
        except Exception as e:
            logger.error(f"Mann-Whitney U test failed: {e}")
            result["test_type"] = "error"
            result["p_value"] = 1.0
            result["effect_size"] = 0.0
            result["effect_size_type"] = "none"
    
    # SC-002: Flag result as statistically significant only if p < 0.05
    result["is_significant"] = result["p_value"] < 0.05
    
    return result

def run_full_analysis(data_path: str, output_path: str) -> Dict[str, Any]:
    """
    Run full statistical analysis on a dataset.
    
    Args:
        data_path: Path to the input parquet file containing matched pairs.
        output_path: Path to save the results JSON.
        
    Returns:
        Dictionary containing the analysis results.
    """
    logger.info(f"Loading data from {data_path}")
    try:
        df = pd.read_parquet(data_path)
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        return {"error": str(e), "is_significant": False}

    # Expected columns based on matching output (T025)
    # We assume the matched dataset has 'review_duration' and 'author_type' (or similar group indicator)
    # Let's check for common column names or raise an error if not found
    required_cols = ['review_duration', 'author_type']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return {"error": f"Missing columns: {missing_cols}", "is_significant": False}

    # Separate groups
    # Assuming author_type distinguishes 'LLM-like' vs 'Human'
    # We need to identify which values correspond to which group.
    # Let's assume 'LLM-like' and 'Human' are the values.
    if 'LLM-like' not in df['author_type'].values or 'Human' not in df['author_type'].values:
        logger.warning(f"Expected 'LLM-like' and 'Human' in author_type. Found: {df['author_type'].unique()}")
        # Try to infer groups if they are boolean or 0/1
        unique_vals = df['author_type'].unique()
        if len(unique_vals) != 2:
            logger.error("Could not identify two distinct groups for comparison.")
            return {"error": "Could not identify two distinct groups", "is_significant": False}
        # Fallback: just split by unique values
        group_a_val, group_b_val = unique_vals[0], unique_vals[1]
    else:
        group_a_val, group_b_val = 'LLM-like', 'Human'

    group_a = df[df['author_type'] == group_a_val]['review_duration'].dropna().tolist()
    group_b = df[df['author_type'] == group_b_val]['review_duration'].dropna().tolist()

    logger.info(f"Group A ({group_a_val}): {len(group_a)} samples")
    logger.info(f"Group B ({group_b_val}): {len(group_b)} samples")

    if len(group_a) == 0 or len(group_b) == 0:
        logger.error("One or both groups are empty after filtering NaN.")
        return {"error": "Empty group after filtering", "is_significant": False}

    analysis_result = select_and_run_test(group_a, group_b)
    analysis_result["groups"] = {
        "group_a": group_a_val,
        "group_b": group_b_val,
        "n_a": len(group_a),
        "n_b": len(group_b)
    }

    # Save results
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_path, 'w') as f:
        json.dump(analysis_result, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    return analysis_result

def main():
    config = get_config()
    # Default paths if not provided in args
    data_path = config.get('paths', {}).get('matched_data', 'data/processed/matched_pairs.parquet')
    output_path = config.get('paths', {}).get('analysis_results', 'data/processed/statistical_analysis_results.json')
    
    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
        
    result = run_full_analysis(data_path, output_path)
    
    # Print summary to stdout for easy verification
    print(f"Analysis Complete.")
    print(f"Test Type: {result.get('test_type', 'N/A')}")
    print(f"P-Value: {result.get('p_value', 'N/A')}")
    print(f"Effect Size: {result.get('effect_size', 'N/A')} ({result.get('effect_size_type', 'N/A')})")
    print(f"Statistically Significant (p < 0.05): {result.get('is_significant', False)}")

    if result.get('error'):
        print(f"Error: {result['error']}")
        sys.exit(1)

if __name__ == "__main__":
    main()