import numpy as np
import pandas as pd
from statsmodels.regression.mixed_linear_model import MixedLM
from typing import Dict, Tuple, List, Optional
import warnings
import json
from pathlib import Path
import sys

# Ensure parent directory is in path for relative imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

def bootstrap_cohen_d(
    group1: np.ndarray,
    group2: np.ndarray,
    n_resamples: int = 10000,
    seed: Optional[int] = None
) -> Dict[str, float]:
    """
    Computes Cohen's d effect size with bootstrapped confidence intervals.
    
    Args:
        group1: Array of values for the first group (e.g., baseline).
        group2: Array of values for the second group (e.g., treatment).
        n_resamples: Number of bootstrap resamples.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing 'cohen_d', 'ci_lower', 'ci_upper'.
    """
    if seed is not None:
        np.random.seed(seed)
        
    n1 = len(group1)
    n2 = len(group2)
    
    if n1 == 0 or n2 == 0:
        raise ValueError("Groups cannot be empty.")
        
    # Calculate original Cohen's d
    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        raise ValueError("Pooled standard deviation is zero; cannot compute Cohen's d.")
        
    cohen_d_orig = (mean1 - mean2) / pooled_std
    
    # Bootstrap resampling
    bootstrap_dists = []
    for _ in range(n_resamples):
        # Resample with replacement
        sample1 = np.random.choice(group1, size=n1, replace=True)
        sample2 = np.random.choice(group2, size=n2, replace=True)
        
        m1, m2 = np.mean(sample1), np.mean(sample2)
        v1, v2 = np.var(sample1, ddof=1), np.var(sample2, ddof=1)
        
        # Handle zero variance in resamples
        pooled_std_boot = np.sqrt(((n1 - 1) * v1 + (n2 - 1) * v2) / (n1 + n2 - 2))
        if pooled_std_boot == 0:
            continue 
            
        d_boot = (m1 - m2) / pooled_std_boot
        bootstrap_dists.append(d_boot)
        
    bootstrap_dists = np.array(bootstrap_dists)
    ci_lower = np.percentile(bootstrap_dists, 2.5)
    ci_upper = np.percentile(bootstrap_dists, 97.5)
    
    return {
        "cohen_d": float(cohen_d_orig),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper)
    }

def bootstrap_odds_ratio(
    contingency_table: np.ndarray,
    n_resamples: int = 10000,
    seed: Optional[int] = None
) -> Dict[str, float]:
    """
    Computes Odds Ratio with bootstrapped confidence intervals from a 2x2 contingency table.
    Table format: [[a, b], [c, d]] where a=success_treat, b=fail_treat, c=success_ctrl, d=fail_ctrl
    
    Args:
        contingency_table: 2x2 numpy array of counts.
        n_resamples: Number of bootstrap resamples.
        seed: Random seed for reproducibility.
        
    Returns:
        Dictionary containing 'odds_ratio', 'ci_lower', 'ci_upper'.
    """
    if seed is not None:
        np.random.seed(seed)
        
    if contingency_table.shape != (2, 2):
        raise ValueError("Contingency table must be 2x2.")
        
    a, b = contingency_table[0]
    c, d = contingency_table[1]
    
    # Original Odds Ratio
    if a * d == 0 or b * c == 0:
        # Add small epsilon to avoid division by zero if needed, or handle specifically
        # Standard practice: add 0.5 to all cells (Haldane-Anscombe correction) if 0 exists
        adj_a, adj_b, adj_c, adj_d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
        or_orig = (adj_a * adj_d) / (adj_b * adj_c)
    else:
        or_orig = (a * d) / (b * c)
        
    total_n = a + b + c + d
    # Probabilities for multinomial resampling
    probs = contingency_table.flatten() / total_n
    
    bootstrap_ors = []
    for _ in range(n_resamples):
        # Resample counts from multinomial distribution
        resampled_counts = np.random.multinomial(total_n, probs)
        ra, rb, rc, rd = resampled_counts
        
        if (rb * rc) == 0:
            # Apply correction again if resample hits zero
            adj_ra, adj_rb, adj_rc, adj_rd = ra + 0.5, rb + 0.5, rc + 0.5, rd + 0.5
            or_boot = (adj_ra * adj_rd) / (adj_rb * adj_rc)
        else:
            or_boot = (ra * rd) / (rb * rc)
            
        bootstrap_ors.append(or_boot)
        
    bootstrap_ors = np.array(bootstrap_ors)
    # Log-normal CI is often preferred for OR, but percentile method is robust for large N
    ci_lower = np.percentile(bootstrap_ors, 2.5)
    ci_upper = np.percentile(bootstrap_ors, 97.5)
    
    return {
        "odds_ratio": float(or_orig),
        "ci_lower": float(ci_lower),
        "ci_upper": float(ci_upper)
    }

def run_lme_model(
    df: pd.DataFrame,
    formula: str,
    subject_col: str = 'participant_id',
    seed: Optional[int] = None
) -> Dict[str, any]:
    """
    Runs a Linear Mixed-Effects model.
    
    Args:
        df: DataFrame containing the data.
        formula: Statsmodels formula string (e.g., "time ~ condition + (1|participant_id)").
        subject_col: Name of the column representing the random effect grouping.
        seed: Random seed (mostly for reproducibility of starting values if needed).
        
    Returns:
        Dictionary with model summary statistics (p-values, coefficients).
    """
    if seed is not None:
        np.random.seed(seed)
        
    # Ensure formula uses the correct subject column if provided explicitly
    # Statsmodels formula syntax: "dependent ~ independent + (1|group)"
    
    try:
        model = MixedLM.from_formula(formula, groups=df[subject_col], data=df)
        result = model.fit()
        
        # Extract key stats
        # P-values are in result.pvalues
        # Coefficients in result.params
        
        p_values = result.pvalues.to_dict()
        params = result.params.to_dict()
        
        # Check for convergence warnings
        warnings.simplefilter("always")
        
        return {
            "coefficients": params,
            "p_values": p_values,
            "converged": result.converged,
            "log_likelihood": result.llf
        }
    except Exception as e:
        # Fallback or re-raise with context
        raise RuntimeError(f"LME Model fitting failed: {str(e)}")

def compute_confidence_interval(
    data: np.ndarray,
    stat_func,
    n_resamples: int = 10000,
    alpha: float = 0.05,
    seed: Optional[int] = None
) -> Tuple[float, float]:
    """
    Generic bootstrap confidence interval for any statistic.
    
    Args:
        data: Input data array.
        stat_func: Function that computes the statistic from the data.
        n_resamples: Number of bootstrap resamples.
        alpha: Significance level (0.05 for 95% CI).
        seed: Random seed.
        
    Returns:
        Tuple of (lower_bound, upper_bound).
    """
    if seed is not None:
        np.random.seed(seed)
        
    n = len(data)
    bootstrap_stats = []
    
    for _ in range(n_resamples):
        resample = np.random.choice(data, size=n, replace=True)
        stat = stat_func(resample)
        bootstrap_stats.append(stat)
        
    bootstrap_stats = np.array(bootstrap_stats)
    lower = np.percentile(bootstrap_stats, 100 * (alpha / 2))
    upper = np.percentile(bootstrap_stats, 100 * (1 - alpha / 2))
    
    return float(lower), float(upper)

def main():
    """
    Main entry point for testing/bootstrap demonstration.
    This script is intended to be imported by run_statistics.py.
    """
    print("Bootstrap utilities loaded successfully.")
    print("Available functions: bootstrap_cohen_d, bootstrap_odds_ratio, run_lme_model, compute_confidence_interval")
    
    # Example usage (commented out to avoid execution on import)
    # group1 = np.random.normal(0, 1, 100)
    # group2 = np.random.normal(0.5, 1, 100)
    # result = bootstrap_cohen_d(group1, group2, seed=42)
    # print(f"Example Cohen's d: {result}")

if __name__ == "__main__":
    main()