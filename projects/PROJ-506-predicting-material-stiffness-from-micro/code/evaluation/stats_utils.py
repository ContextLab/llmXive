"""
Statistical utilities for evaluation.
Implements One-way ANOVA and Tukey HSD as per amended spec.
"""
import numpy as np
from scipy import stats
from typing import List, Dict, Tuple

def compute_one_way_anova(groups: Dict[str, List[float]]) -> Tuple[float, float]:
    """
    Perform One-way ANOVA test.
    
    Args:
        groups: Dictionary mapping group names to lists of values
        
    Returns:
        Tuple of (F-statistic, p-value)
    """
    group_values = list(groups.values())
    f_stat, p_val = stats.f_oneway(*group_values)
    return f_stat, p_val

def compute_tukey_hsd(values: List[float], groups: List[str], alpha: float = 0.05) -> Dict:
    """
    Perform Tukey HSD post-hoc test.
    
    Args:
        values: List of all values
        groups: List of group labels for each value
        alpha: Significance level
        
    Returns:
        Dictionary with test results
    """
    from statsmodels.stats.multicomp import pairwise_tukeyhsd
    
    tukey = pairwise_tukeyhsd(endog=values, groups=groups, alpha=alpha)
    
    return {
        "reject": tukey.reject,
        "pvalues": tukey.pvalues,
        "meandiffs": tukey.meandiffs,
        "confint": tukey.confint
    }

def compute_degradation_rate(densities: List[float], errors: List[float]) -> float:
    """
    Calculate degradation rate (slope of MAE vs density for OOD).
    
    Args:
        densities: List of inclusion densities
        errors: List of prediction errors (MAE)
        
    Returns:
        Slope of linear regression (MAE per % density)
    """
    if len(densities) < 2:
        return 0.0
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(densities, errors)
    return float(slope)

def main():
    """Demo of statistical functions."""
    # Example usage
    groups = {
        "low_density": [0.1, 0.15, 0.12],
        "medium_density": [0.25, 0.28, 0.26],
        "high_density": [0.45, 0.48, 0.46]
    }
    
    f_stat, p_val = compute_one_way_anova(groups)
    print(f"ANOVA F-statistic: {f_stat:.4f}, p-value: {p_val:.4f}")

if __name__ == "__main__":
    main()
