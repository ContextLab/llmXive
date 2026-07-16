"""
Metrics calculation module for bootstrap analysis.

Provides functions to calculate coverage probability, CI width stability,
bias estimation, and statistical significance tests.
"""
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from scipy import stats
from statsmodels.stats.contingency_tables import mcnemar
from config import get_data_seed, get_bootstrap_seed, get_shuffle_seed


def calculate_coverage(cis: List[Tuple[float, float]], true_mean: float) -> float:
    """
    Calculate empirical coverage probability.
    
    Args:
        cis: List of confidence intervals as (lower, upper) tuples.
        true_mean: Theoretical true mean to check coverage against.
    
    Returns:
        Coverage probability as a float between 0 and 1.
    """
    if not cis:
        return 0.0
    
    covered = sum(1 for lower, upper in cis if lower <= true_mean <= upper)
    return covered / len(cis)


def calculate_ci_width_stability(ordered_cis: List[Tuple[float, float]], 
                                 shuffled_cis: List[Tuple[float, float]]) -> float:
    """
    Calculate the ratio of CI widths between ordered and shuffled data.
    
    Args:
        ordered_cis: List of CIs from ordered (temporal) data.
        shuffled_cis: List of CIs from shuffled data.
    
    Returns:
        Ratio of mean CI widths (ordered / shuffled).
    """
    if not ordered_cis or not shuffled_cis:
        return 1.0
    
    ordered_widths = [upper - lower for lower, upper in ordered_cis]
    shuffled_widths = [upper - lower for lower, upper in shuffled_cis]
    
    mean_ordered = np.mean(ordered_widths)
    mean_shuffled = np.mean(shuffled_widths)
    
    if mean_shuffled == 0:
        return 1.0
    
    return mean_ordered / mean_shuffled


def calculate_bias_block_bootstrap(ordered_cis: List[Tuple[float, float]], 
                                   block_cis: List[Tuple[float, float]]) -> float:
    """
    Calculate bias estimate comparing ordered and block bootstrap results.
    
    Args:
        ordered_cis: CIs from standard bootstrap on ordered data.
        block_cis: CIs from block bootstrap (treated as more accurate).
    
    Returns:
        Estimated bias as the difference in mean CI centers.
    """
    if not ordered_cis or not block_cis:
        return 0.0
    
    ordered_centers = [(lower + upper) / 2 for lower, upper in ordered_cis]
    block_centers = [(lower + upper) / 2 for lower, upper in block_cis]
    
    return np.mean(ordered_centers) - np.mean(block_centers)


def mcnemar_test_logic(ordered_covered: List[bool], shuffled_covered: List[bool]) -> float:
    """
    Perform McNemar's test for paired binary outcomes.
    
    Args:
        ordered_covered: Boolean list indicating if ordered CI covered true mean.
        shuffled_covered: Boolean list indicating if shuffled CI covered true mean.
    
    Returns:
        P-value from McNemar's test.
    
    Raises:
        ValueError: If lists are not of equal length or empty.
    """
    if len(ordered_covered) != len(shuffled_covered):
        raise ValueError("Covered lists must be of equal length")
    
    if not ordered_covered:
        raise ValueError("Covered lists cannot be empty")
    
    # Build contingency table
    # Rows: Ordered (Covered, Not Covered)
    # Cols: Shuffled (Covered, Not Covered)
    a = sum(1 for o, s in zip(ordered_covered, shuffled_covered) if o and s)
    b = sum(1 for o, s in zip(ordered_covered, shuffled_covered) if o and not s)
    c = sum(1 for o, s in zip(ordered_covered, shuffled_covered) if not o and s)
    d = sum(1 for o, s in zip(ordered_covered, shuffled_covered) if not o and not s)
    
    contingency_table = np.array([[a, b], [c, d]])
    
    # Perform McNemar's test
    result = mcnemar(contingency_table, exact=True)
    return result.pvalue


def calculate_coverage_drop_magnitude(empirical_coverage: float, 
                                      target_coverage: float = 0.95) -> float:
    """
    Calculate the magnitude of coverage drop from target.
    
    Args:
        empirical_coverage: Observed coverage probability.
        target_coverage: Target coverage (default 0.95).
    
    Returns:
        Absolute difference between target and empirical coverage.
    """
    return abs(target_coverage - empirical_coverage)


def stratify_by_phi(results: List[Dict[str, Any]], bins: List[float]) -> Dict[str, Any]:
    """
    Stratify simulation results by estimated phi values.
    
    Args:
        results: List of result dictionaries containing 'phi' and metrics.
        bins: List of bin edges for stratification.
    
    Returns:
        Dictionary with stratified summary statistics.
    """
    if not results:
        return {}
    
    phi_values = [r['phi'] for r in results]
    bin_labels = [f"{bins[i]:.1f}-{bins[i+1]:.1f}" for i in range(len(bins)-1)]
    
    stratified = {}
    for i in range(len(bins) - 1):
        bin_mask = (np.array(phi_values) >= bins[i]) & (np.array(phi_values) < bins[i+1])
        if i == len(bins) - 2:  # Last bin includes right edge
            bin_mask = (np.array(phi_values) >= bins[i]) & (np.array(phi_values) <= bins[i+1])
        
        bin_results = [r for r, m in zip(results, bin_mask) if m]
        
        if bin_results:
            stratified[bin_labels[i]] = {
                'count': len(bin_results),
                'mean_coverage': np.mean([r['coverage'] for r in bin_results]),
                'mean_ci_width': np.mean([r['ci_width'] for r in bin_results]),
                'mean_p_value': np.mean([r['p_value'] for r in bin_results])
            }
    
    return stratified
