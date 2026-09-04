import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_shapiro_wilk(data: np.ndarray) -> Tuple[float, float]:
    """
    Perform Shapiro-Wilk test for normality.
    
    Args:
        data: Array of values to test for normality
        
    Returns:
        Tuple of (statistic, p-value)
    """
    if len(data) < 3:
        logger.warning("Shapiro-Wilk requires at least 3 samples. Returning (1.0, 1.0).")
        return 1.0, 1.0
    
    try:
        stat, p_value = stats.shapiro(data)
        return stat, p_value
    except Exception as e:
        logger.error(f"Shapiro-Wilk test failed: {e}")
        raise

def calculate_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size.
    
    Args:
        group1: First group of values
        group2: Second group of values
        
    Returns:
        Cohen's d value
    """
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    
    # Pooled standard deviation
    n1, n2 = len(group1), len(group2)
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        logger.warning("Pooled standard deviation is zero. Returning 0.0 for Cohen's d.")
        return 0.0
        
    return (mean1 - mean2) / pooled_std

def calculate_rank_biserial(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate rank-biserial correlation for Mann-Whitney U test.
    
    Args:
        group1: First group of values
        group2: Second group of values
        
    Returns:
        Rank-biserial correlation value
    """
    try:
        u_stat, _ = stats.mannwhitneyu(group1, group2, alternative='two-sided')
        n1, n2 = len(group1), len(group2)
        # Rank-biserial correlation formula
        r = 1 - (2 * u_stat) / (n1 * n2)
        return r
    except Exception as e:
        logger.error(f"Rank-biserial calculation failed: {e}")
        return 0.0

def select_and_run_test(group1: np.ndarray, group2: np.ndarray, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Select appropriate statistical test based on normality and run it.
    
    Args:
        group1: First group of values
        group2: Second group of values
        alpha: Significance level for normality test
        
    Returns:
        Dictionary containing test results
    """
    logger.info("Running Shapiro-Wilk normality test...")
    _, p_normality = run_shapiro_wilk(np.concatenate([group1, group2]))
    
    is_normal = p_normality > alpha
    logger.info(f"Normality test p-value: {p_normality:.4f} (Normal: {is_normal})")
    
    result = {
        "normality_p_value": p_normality,
        "is_normal": is_normal,
        "test_type": "t-test" if is_normal else "mann-whitney-u"
    }
    
    if is_normal:
        # Independent samples t-test
        stat, p_value = stats.ttest_ind(group1, group2, equal_var=True)
        result["test_statistic"] = float(stat)
        result["p_value"] = float(p_value)
        result["cohen_d"] = float(calculate_cohens_d(group1, group2))
    else:
        # Mann-Whitney U test
        stat, p_value = stats.mannwhitneyu(group1, group2, alternative='two-sided')
        result["test_statistic"] = float(stat)
        result["p_value"] = float(p_value)
        result["rank_biserial"] = float(calculate_rank_biserial(group1, group2))
    
    # T026 Implementation: Flag as statistically significant only if p < 0.05
    result["is_statistically_significant"] = result["p_value"] < 0.05
    
    return result

def run_full_analysis(
    matched_data: pd.DataFrame,
    treatment_col: str = "review_duration",
    group_col: str = "generation_source",
    treatment_value: str = "LLM",
    control_value: str = "Human"
) -> Dict[str, Any]:
    """
    Run full statistical analysis on matched data.
    
    Args:
        matched_data: DataFrame containing matched pairs with review durations
        treatment_col: Name of column containing the outcome variable
        group_col: Name of column indicating group assignment
        treatment_value: Value in group_col representing treatment group
        control_value: Value in group_col representing control group
        
    Returns:
        Dictionary containing full analysis results
    """
    logger.info("Loading matched data for statistical analysis...")
    
    # Filter groups
    treatment_group = matched_data[matched_data[group_col] == treatment_value][treatment_col].values
    control_group = matched_data[matched_data[group_col] == control_value][treatment_col].values
    
    if len(treatment_group) == 0 or len(control_group) == 0:
        raise ValueError("One or both groups are empty after filtering.")
    
    logger.info(f"Treatment group size: {len(treatment_group)}, Control group size: {len(control_group)}")
    
    # Run statistical test
    results = select_and_run_test(treatment_group, control_group)
    
    # Add group statistics
    results["treatment_mean"] = float(np.mean(treatment_group))
    results["treatment_std"] = float(np.std(treatment_group, ddof=1))
    results["control_mean"] = float(np.mean(control_group))
    results["control_std"] = float(np.std(control_group, ddof=1))
    results["treatment_n"] = len(treatment_group)
    results["control_n"] = len(control_group)
    
    return results

def main():
    """
    Main entry point for statistical analysis.
    Reads matched data, performs analysis, and outputs results.
    """
    # Default paths
    input_path = Path("data/processed/matched_pairs.parquet")
    output_path = Path("data/processed/analysis_results.json")
    
    # Allow CLI overrides
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_path = Path(sys.argv[2])
        
    logger.info(f"Input data: {input_path}")
    logger.info(f"Output results: {output_path}")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Load data
    try:
        df = pd.read_parquet(input_path)
    except Exception as e:
        logger.error(f"Failed to load parquet file: {e}")
        sys.exit(1)
    
    # Run analysis
    try:
        results = run_full_analysis(df)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save results
    try:
        import json
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {output_path}")
        logger.info(f"Statistically Significant (p < 0.05): {results['is_statistically_significant']}")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        sys.exit(1)
    
    return results

if __name__ == "__main__":
    main()