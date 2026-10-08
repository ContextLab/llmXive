import numpy as np
import pandas as pd
from scipy import stats
from typing import Tuple, Dict, Any, List, Optional
import logging
import json
import os

logger = logging.getLogger(__name__)

def select_test_statistic(outcome_type: str) -> str:
    """Select the appropriate statistical test based on outcome type.
    
    Args:
        outcome_type: Either 'continuous' or 'binary'
        
    Returns:
        String identifier for the test ('ttest' or 'wilcoxon')
    """
    if outcome_type == 'continuous':
        return 'ttest'
    elif outcome_type == 'binary':
        return 'wilcoxon'
    else:
        raise ValueError(f"Unknown outcome type: {outcome_type}")

def run_statistical_test(data: pd.DataFrame, treatment_col: str, outcome_col: str, 
                         test_type: str) -> float:
    """Run the appropriate statistical test and return the p-value.
    
    Args:
        data: DataFrame containing the data
        treatment_col: Name of the treatment column
        outcome_col: Name of the outcome column
        test_type: 'ttest' or 'wilcoxon'
        
    Returns:
        p-value from the test
    """
    # Split data by treatment group
    treated = data[data[treatment_col] == 1][outcome_col]
    control = data[data[treatment_col] == 0][outcome_col]
    
    if len(treated) == 0 or len(control) == 0:
        logger.warning("One of the treatment groups is empty. Returning p=1.0")
        return 1.0
    
    if test_type == 'ttest':
        stat, p_val = stats.ttest_ind(treated, control)
    elif test_type == 'wilcoxon':
        # Wilcoxon rank-sum test (Mann-Whitney U) for independent samples
        stat, p_val = stats.mannwhitneyu(treated, control, alternative='two-sided')
    else:
        raise ValueError(f"Unknown test type: {test_type}")
        
    return float(p_val)

def calculate_type1_error(p_values: List[float], alpha: float = 0.05) -> float:
    """Calculate the empirical Type I error rate.
    
    Type I error rate is the proportion of times we reject the null hypothesis
    when it is true (p < alpha).
    
    Args:
        p_values: List of p-values from simulation iterations
        alpha: Significance level threshold
        
    Returns:
        Empirical Type I error rate
    """
    if not p_values:
        logger.warning("Empty p-values list. Returning 0.0 for Type I error.")
        return 0.0
        
    significant_count = sum(1 for p in p_values if p < alpha)
    return significant_count / len(p_values)

def calculate_power(p_values: List[float], alpha: float = 0.05) -> float:
    """Calculate statistical power (1 - Type II error).
    
    Under the alternative hypothesis, power is the proportion of times
    we correctly reject the null hypothesis.
    
    Args:
        p_values: List of p-values from simulation iterations
        alpha: Significance level threshold
        
    Returns:
        Statistical power
    """
    if not p_values:
        logger.warning("Empty p-values list. Returning 0.0 for power.")
        return 0.0
        
    significant_count = sum(1 for p in p_values if p < alpha)
    return significant_count / len(p_values)

def aggregate_results(p_values: List[float], config: Dict[str, Any], 
                     dataset_info: Dict[str, Any], method: str = "CC") -> Dict[str, Any]:
    """Aggregate simulation results into a structured format.
    
    Args:
        p_values: List of p-values from all iterations
        config: Simulation configuration dictionary
        dataset_info: Information about the dataset used
        method: Analysis method used (e.g., "CC", "MI", "IPW")
        
    Returns:
        Dictionary containing aggregated results
    """
    if not p_values:
        logger.warning("No p-values to aggregate.")
        return {
            "empirical_type1_error": 0.0,
            "p_value_distribution": {"bins": [], "counts": [], "total": 0},
            "total_iterations": 0,
            "significant_count": 0,
            "method_used": method,
            "config": config,
            "dataset_info": dataset_info
        }
        
    # Calculate Type I error rate
    type1_error = calculate_type1_error(p_values)
    
    # Create p-value distribution histogram
    bins = [i * 0.1 for i in range(11)]  # 0.0, 0.1, ..., 1.0
    counts = [0] * 10
    for p in p_values:
        if p < 1.0:
            bin_idx = int(p * 10)
            counts[bin_idx] += 1
        else:
            counts[9] += 1  # Put p=1.0 in the last bin
    
    return {
        "empirical_type1_error": type1_error,
        "p_value_distribution": {
            "bins": bins,
            "counts": counts,
            "total": len(p_values)
        },
        "total_iterations": len(p_values),
        "significant_count": sum(1 for p in p_values if p < 0.05),
        "method_used": method,
        "config": config,
        "dataset_info": dataset_info
    }

def compare_to_nominal(results: Dict[str, Any], nominal_alpha: float = 0.05, 
                      relative_threshold: float = 0.10) -> Dict[str, Any]:
    """Detect when the empirical error rate exceeds the nominal level by a relative margin.
    
    This function implements the sensitivity analysis check for User Story 2.
    It determines if the Complete-Case (CC) method's empirical Type I error rate
    exceeds the threshold defined as a relative increase over the nominal alpha.
    
    Threshold = nominal_alpha * (1 + relative_threshold)
    For nominal_alpha=0.05 and relative_threshold=0.10, threshold = 0.055.
    
    Args:
        results: Dictionary containing simulation results (from aggregate_results)
        nominal_alpha: The nominal significance level (default 0.05)
        relative_threshold: The relative increase threshold (default 0.10 for 10%)
        
    Returns:
        Dictionary with:
            - 'exceeds_threshold': bool indicating if error rate is too high
            - 'empirical_error': the observed error rate
            - 'threshold': the calculated threshold value
            - 'relative_increase': the relative increase observed
            - 'method': the analysis method used
            - 'config': the simulation config used
    """
    empirical_error = results.get("empirical_type1_error", 0.0)
    method = results.get("method_used", "Unknown")
    config = results.get("config", {})
    
    threshold = nominal_alpha * (1 + relative_threshold)
    relative_increase = (empirical_error - nominal_alpha) / nominal_alpha if nominal_alpha > 0 else 0
    
    exceeds = empirical_error > threshold
    
    logger.info(
        f"Comparing to nominal: method={method}, "
        f"empirical_error={empirical_error:.4f}, "
        f"threshold={threshold:.4f}, "
        f"exceeds={exceeds}"
    )
    
    return {
        "exceeds_threshold": exceeds,
        "empirical_error": empirical_error,
        "threshold": threshold,
        "relative_increase": relative_increase,
        "method": method,
        "config": config,
        "nominal_alpha": nominal_alpha
    }

def apply_fdr_correction(p_values: List[float], method: str = 'benjamini_hochberg') -> List[float]:
    """Apply False Discovery Rate correction to a list of p-values.
    
    Uses the Benjamini-Hochberg procedure by default.
    
    Args:
        p_values: List of raw p-values
        method: Correction method ('benjamini_hochberg' or 'fdr_bh')
        
    Returns:
        List of adjusted p-values
    """
    if not p_values:
        return []
        
    # Use scipy's multipletests for FDR correction
    from statsmodels.stats.multitest import multipletests
    
    corrected = multipletests(p_values, method=method)
    return list(corrected[1])  # Return adjusted p-values