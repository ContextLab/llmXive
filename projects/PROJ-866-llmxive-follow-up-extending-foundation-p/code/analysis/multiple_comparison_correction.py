"""
Multiple Comparison Correction Module for Trade-off Analysis.

Implements Bonferroni and Benjamini-Hochberg (BH) corrections for
multiple hypothesis testing in the context of policy violation analysis.

This module provides functions to correct p-values obtained from statistical
tests performed across multiple workflow compression levels or depths,
ensuring robust identification of the safe operating zone.
"""

import numpy as np
from typing import List, Tuple, Dict, Optional, Any
import warnings


def bonferroni_correction(p_values: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply Bonferroni correction to a set of p-values.

    The Bonferroni correction is a conservative method that controls the
    Family-Wise Error Rate (FWER) by multiplying each p-value by the
    number of tests performed.

    Parameters
    ----------
    p_values : np.ndarray
        Array of uncorrected p-values (1D array).
    alpha : float, optional
        Significance level (default: 0.05).

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        - Corrected p-values (clipped to max 1.0)
        - Boolean array indicating which hypotheses are rejected (significant)
          after correction.

    Notes
    -----
    The Bonferroni correction is simple but can be overly conservative,
    especially when tests are correlated. It is suitable for small numbers
    of comparisons.
    """
    if p_values.ndim != 1:
        raise ValueError("p_values must be a 1D array")
    
    n_tests = len(p_values)
    if n_tests == 0:
        return p_values.copy(), np.array([], dtype=bool)
    
    # Bonferroni: multiply p-values by number of tests
    corrected_p = p_values * n_tests
    corrected_p = np.clip(corrected_p, 0.0, 1.0)
    
    # Determine significance
    significant = corrected_p < alpha
    
    return corrected_p, significant


def benjamini_hochberg_correction(
    p_values: np.ndarray, 
    alpha: float = 0.05,
    method: str = 'indep'
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply Benjamini-Hochberg (BH) correction to control False Discovery Rate (FDR).

    The BH procedure is less conservative than Bonferroni and controls the
    expected proportion of false discoveries among rejected hypotheses.

    Parameters
    ----------
    p_values : np.ndarray
        Array of uncorrected p-values (1D array).
    alpha : float, optional
        Significance level (default: 0.05).
    method : str, optional
        Method for FDR control:
        - 'indep': Assumes independent or positively dependent tests (standard BH)
        - 'negcorr': For negative dependence (Benjamini-Yekutieli)

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        - Corrected p-values (FDR-adjusted)
        - Boolean array indicating which hypotheses are rejected (significant)
          after correction.

    Notes
    -----
    The BH procedure sorts p-values and compares each to a progressively
    increasing threshold. It is more powerful than Bonferroni when dealing
    with many correlated tests.
    """
    if p_values.ndim != 1:
        raise ValueError("p_values must be a 1D array")
    
    n_tests = len(p_values)
    if n_tests == 0:
        return p_values.copy(), np.array([], dtype=bool)
    
    # Handle NaN values
    nan_mask = np.isnan(p_values)
    if np.any(nan_mask):
        warnings.warn(f"Found {np.sum(nan_mask)} NaN p-values. They will be treated as non-significant.")
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Create rank array (1-indexed)
    ranks = np.arange(1, n_tests + 1)
    
    # Calculate BH thresholds
    if method == 'indep':
        # Standard BH: p_i * n / i
        thresholds = (ranks / n_tests) * alpha
    elif method == 'negcorr':
        # Benjamini-Yekutieli for negative dependence
        # Sum of 1/i from 1 to n
        by_factor = np.sum(1.0 / ranks)
        thresholds = (ranks / n_tests) * (alpha / by_factor)
    else:
        raise ValueError(f"Unknown method '{method}'. Use 'indep' or 'negcorr'.")
    
    # Find the largest k such that p_(k) <= threshold_(k)
    # Work backwards from the largest p-value
    reject_mask = sorted_p <= thresholds
    
    if not np.any(reject_mask):
        # No rejections
        corrected_p = np.full(n_tests, 1.0)
        significant = np.zeros(n_tests, dtype=bool)
    else:
        # Find the largest index where rejection occurs
        largest_k = np.max(np.where(reject_mask)[0])
        
        # All hypotheses with index <= largest_k are rejected
        reject_mask_cumulative = np.zeros(n_tests, dtype=bool)
        reject_mask_cumulative[:largest_k + 1] = True
        
        # Calculate adjusted p-values
        # The adjusted p-value for sorted p_i is max(p_j * n / j for j >= i)
        # But we can use the simpler approach: adjusted p_i = min(1, p_i * n / rank_i)
        # with monotonicity constraint
        
        adjusted_p = sorted_p * n_tests / ranks
        adjusted_p = np.clip(adjusted_p, 0.0, 1.0)
        
        # Ensure monotonicity (adjusted p-values should be non-decreasing with rank)
        # Work backwards to enforce this
        for i in range(n_tests - 2, -1, -1):
            adjusted_p[i] = min(adjusted_p[i], adjusted_p[i + 1])
        
        # Map back to original order
        corrected_p = np.zeros(n_tests)
        corrected_p[sorted_indices] = adjusted_p
        significant = reject_mask_cumulative[sorted_indices]
    
    return corrected_p, significant


def apply_correction(
    p_values: np.ndarray,
    alpha: float = 0.05,
    method: str = 'bh'
) -> Dict[str, Any]:
    """
    Apply multiple comparison correction using the specified method.

    Parameters
    ----------
    p_values : np.ndarray
        Array of uncorrected p-values.
    alpha : float, optional
        Significance level (default: 0.05).
    method : str, optional
        Correction method: 'bonferroni' or 'bh' (Benjamini-Hochberg).

    Returns
    -------
    Dict[str, Any]
        Dictionary containing:
        - 'original_p': Original p-values
        - 'corrected_p': Corrected p-values
        - 'significant': Boolean array of significant results
        - 'method': The correction method used
        - 'alpha': The significance level used
        - 'n_tests': Number of tests performed

    Raises
    ------
    ValueError
        If an unknown correction method is specified.
    """
    p_values = np.asarray(p_values)
    
    if method.lower() == 'bonferroni':
        corrected_p, significant = bonferroni_correction(p_values, alpha)
    elif method.lower() in ['bh', 'fdr', 'benjamini_hochberg']:
        corrected_p, significant = benjamini_hochberg_correction(p_values, alpha)
    else:
        raise ValueError(f"Unknown correction method: {method}. Use 'bonferroni' or 'bh'.")
    
    return {
        'original_p': p_values.tolist(),
        'corrected_p': corrected_p.tolist(),
        'significant': significant.tolist(),
        'method': method,
        'alpha': alpha,
        'n_tests': len(p_values)
    }


def calculate_fdr_threshold(
    p_values: np.ndarray,
    q: float = 0.05
) -> float:
    """
    Calculate the BH threshold for a given FDR level q.

    This function returns the maximum p-value that would be considered
    significant at the specified FDR level.

    Parameters
    ----------
    p_values : np.ndarray
        Array of p-values.
    q : float, optional
        Target FDR level (default: 0.05).

    Returns
    -------
    float
        The p-value threshold for significance. Returns 0.0 if no
        hypotheses are rejected.
    """
    p_values = np.asarray(p_values)
    n_tests = len(p_values)
    
    if n_tests == 0:
        return 0.0
    
    # Sort p-values
    sorted_p = np.sort(p_values)
    ranks = np.arange(1, n_tests + 1)
    
    # Find largest k where p_(k) <= (k/n) * q
    thresholds = (ranks / n_tests) * q
    valid = sorted_p <= thresholds
    
    if not np.any(valid):
        return 0.0
    
    largest_k = np.max(np.where(valid)[0])
    return sorted_p[largest_k]


def main():
    """
    Demonstration of multiple comparison correction methods.
    """
    print("Multiple Comparison Correction Demonstration")
    print("=" * 50)
    
    # Example: Simulated p-values from hypothesis tests at different compression levels
    np.random.seed(42)
    n_tests = 20
    # Simulate some significant and non-significant p-values
    true_p = np.random.uniform(0.0, 1.0, n_tests)
    # Make some definitely significant
    true_p[0:3] = np.random.uniform(0.001, 0.02, 3)
    # Make some borderline
    true_p[3:5] = np.random.uniform(0.04, 0.06, 2)
    
    print(f"\nOriginal p-values (n={n_tests}):")
    print(true_p)
    
    # Bonferroni correction
    print("\n--- Bonferroni Correction ---")
    corrected_bonf, sig_bonf = bonferroni_correction(true_p, alpha=0.05)
    print(f"Corrected p-values: {corrected_bonf}")
    print(f"Significant (alpha=0.05): {sig_bonf}")
    print(f"Number of rejections: {np.sum(sig_bonf)}")
    
    # Benjamini-Hochberg correction
    print("\n--- Benjamini-Hochberg Correction ---")
    corrected_bh, sig_bh = benjamini_hochberg_correction(true_p, alpha=0.05)
    print(f"Corrected p-values: {corrected_bh}")
    print(f"Significant (alpha=0.05): {sig_bh}")
    print(f"Number of rejections: {np.sum(sig_bh)}")
    
    # Compare with uncorrected
    sig_uncorrected = true_p < 0.05
    print(f"\nUncorrected significant: {np.sum(sig_uncorrected)}")
    print(f"Bonferroni significant: {np.sum(sig_bonf)}")
    print(f"BH significant: {np.sum(sig_bh)}")
    
    # FDR threshold calculation
    print("\n--- FDR Threshold Calculation ---")
    threshold = calculate_fdr_threshold(true_p, q=0.05)
    print(f"Threshold for FDR=0.05: {threshold:.4f}")
    
    print("\n" + "=" * 50)
    print("Demonstration complete.")


if __name__ == "__main__":
    main()