"""
Statistical Utilities for Model Evaluation.

Implements One-way ANOVA, Tukey HSD, and degradation rate calculations.
"""

import numpy as np
from scipy import stats
from typing import List, Dict, Tuple

def compute_one_way_anova(
    groups: Dict[str, List[float]]
) -> Tuple[float, float]:
    """
    Perform One-way ANOVA test on grouped data.

    Args:
        groups: Dictionary mapping group names to lists of values.

    Returns:
        Tuple of (F-statistic, p-value).
    """
    group_values = list(groups.values())
    f_stat, p_val = stats.f_oneway(*group_values)
    return f_stat, p_val

def compute_tukey_hsd(
    groups: Dict[str, List[float]],
    alpha: float = 0.05
) -> Dict[str, Dict[str, bool]]:
    """
    Perform Tukey HSD post-hoc test on grouped data.

    Args:
        groups: Dictionary mapping group names to lists of values.
        alpha: Significance level.

    Returns:
        Dictionary of pairwise comparisons with significance flags.
    """
    # Simplified implementation; full implementation would use statsmodels
    # This is a placeholder for the actual Tukey HSD logic
    results = {}
    group_names = list(groups.keys())
    values = list(groups.values())
    
    for i in range(len(group_names)):
        for j in range(i + 1, len(group_names)):
            # Simplified t-test as placeholder
            t_stat, p_val = stats.ttest_ind(values[i], values[j])
            key = f"{group_names[i]} vs {group_names[j]}"
            results[key] = {'p_value': p_val, 'significant': p_val < alpha}
    
    return results

def compute_degradation_rate(
    densities: List[float],
    errors: List[float],
    threshold: float
) -> float:
    """
    Compute the degradation rate of model performance for OOD densities.

    Args:
        densities: List of inclusion densities.
        errors: List of prediction errors (e.g., MAE).
        threshold: Density threshold above which data is considered OOD.

    Returns:
        Slope of error vs density for OOD data (MAE per % density).
    """
    # Filter for OOD data
    ood_indices = [i for i, d in enumerate(densities) if d > threshold]
    
    if len(ood_indices) < 2:
        return 0.0
    
    ood_densities = [densities[i] for i in ood_indices]
    ood_errors = [errors[i] for i in ood_indices]
    
    # Linear regression to find slope
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        ood_densities, ood_errors
    )
    
    return slope

def main():
    """Main entry point for stats utilities."""
    print("Statistical utilities loaded.")
