"""
Statistical utilities for the llmXive automated science pipeline.

This module provides functions for correlation analysis, p-value calculation,
and multiple-comparison correction as required for the network topology
synchronization research.

Dependencies:
    - scipy: for statistical tests
    - numpy: for numerical operations
"""

import numpy as np
from scipy import stats
from typing import Tuple, List, Union, Optional


def spearman_correlation(
    x: Union[np.ndarray, List[float]],
    y: Union[np.ndarray, List[float]]
) -> Tuple[float, float]:
    """
    Calculate the Spearman rank correlation coefficient and its p-value.

    Parameters
    ----------
    x : array-like
        First dataset (e.g., rewiring probabilities).
    y : array-like
        Second dataset (e.g., critical coupling strengths).

    Returns
    -------
    tuple (rho, p_value)
        rho : float
            Spearman correlation coefficient.
        p_value : float
            The p-value associated with the correlation.

    Raises
    ------
    ValueError
        If input arrays have different lengths or are empty.
    """
    x_arr = np.asarray(x)
    y_arr = np.asarray(y)

    if x_arr.size == 0 or y_arr.size == 0:
        raise ValueError("Input arrays cannot be empty.")
    if x_arr.shape != y_arr.shape:
        raise ValueError("Input arrays must have the same shape.")

    # Use scipy.stats.spearmanr
    # Returns a SpearmanrResult object with 'correlation' and 'pvalue'
    result = stats.spearmanr(x_arr, y_arr)
    return float(result.correlation), float(result.pvalue)


def bonferroni_correction(
    p_values: Union[np.ndarray, List[float]],
    alpha: float = 0.05
) -> Tuple[List[float], List[bool]]:
    """
    Apply the Bonferroni correction for multiple comparisons.

    This method adjusts the p-values by multiplying them by the number of tests
    and compares them against the significance level alpha.

    Parameters
    ----------
    p_values : array-like
        List of raw p-values from statistical tests.
    alpha : float, optional
        Significance level (default is 0.05).

    Returns
    -------
    tuple (adjusted_p_values, significant)
        adjusted_p_values : list of float
            The Bonferroni-corrected p-values.
        significant : list of bool
            Boolean mask indicating which tests are significant after correction.
    """
    p_arr = np.asarray(p_values)
    n_tests = len(p_arr)

    if n_tests == 0:
        return [], []

    # Bonferroni adjustment: p_adj = p * n
    # Clip to 1.0 to ensure valid probability
    adjusted = np.minimum(p_arr * n_tests, 1.0)

    # Determine significance
    significant = adjusted < alpha

    return adjusted.tolist(), significant.tolist()


def benjamini_hochberg_correction(
    p_values: Union[np.ndarray, List[float]],
    alpha: float = 0.05
) -> Tuple[List[float], List[bool]]:
    """
    Apply the Benjamini-Hochberg (BH) procedure for false discovery rate control.

    This method is less conservative than Bonferroni and is suitable when
    multiple hypotheses are tested simultaneously.

    Parameters
    ----------
    p_values : array-like
        List of raw p-values from statistical tests.
    alpha : float, optional
        Significance level (default is 0.05).

    Returns
    -------
    tuple (adjusted_p_values, significant)
        adjusted_p_values : list of float
            The BH-adjusted p-values (q-values).
        significant : list of bool
            Boolean mask indicating which tests are significant after correction.
    """
    p_arr = np.asarray(p_values)
    n_tests = len(p_arr)

    if n_tests == 0:
        return [], []

    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_arr)
    sorted_p = p_arr[sorted_indices]

    # Calculate BH adjusted p-values
    # q_i = p_i * n / i
    # Ensure monotonicity by taking the cumulative minimum from the end
    ranks = np.arange(1, n_tests + 1)
    adjusted_sorted = (sorted_p * n_tests) / ranks
    adjusted_sorted = np.minimum.accumulate(adjusted_sorted[::-1])[::-1]
    adjusted_sorted = np.minimum(adjusted_sorted, 1.0)

    # Restore original order
    adjusted = np.empty(n_tests)
    adjusted[sorted_indices] = adjusted_sorted

    # Determine significance
    # A test is significant if its adjusted p-value is less than alpha
    significant = adjusted < alpha

    return adjusted.tolist(), significant.tolist()


def calculate_correlation_with_correction(
    x: Union[np.ndarray, List[float]],
    y: Union[np.ndarray, List[float]],
    method: str = 'spearman',
    correction: Optional[str] = None,
    alpha: float = 0.05
) -> dict:
    """
    Calculate correlation and optionally apply multiple-comparison correction.

    This is a convenience wrapper that combines correlation calculation with
    correction logic.

    Parameters
    ----------
    x : array-like
        First dataset.
    y : array-like
        Second dataset.
    method : str, optional
        Correlation method ('spearman' or 'pearson'). Default is 'spearman'.
    correction : str, optional
        Correction method ('bonferroni', 'benjamini-hochberg', or None).
    alpha : float, optional
        Significance level for correction.

    Returns
    -------
    dict
        Dictionary containing correlation results and correction status.
        Keys:
            - 'correlation': float
            - 'p_value': float
            - 'adjusted_p_value': float (if correction applied, else None)
            - 'significant': bool (if correction applied, else None)
            - 'correction_method': str (name of correction used, or None)
    """
    if method == 'spearman':
        rho, p_val = spearman_correlation(x, y)
    elif method == 'pearson':
        rho, p_val = stats.pearsonr(x, y)
        rho, p_val = float(rho), float(p_val)
    else:
        raise ValueError(f"Unsupported correlation method: {method}")

    result = {
        'correlation': rho,
        'p_value': p_val,
        'adjusted_p_value': None,
        'significant': None,
        'correction_method': None
    }

    if correction:
        if correction == 'bonferroni':
            adj_p, sig = bonferroni_correction([p_val], alpha)
            result['correction_method'] = 'bonferroni'
        elif correction == 'benjamini-hochberg':
            adj_p, sig = benjamini_hochberg_correction([p_val], alpha)
            result['correction_method'] = 'benjamini-hochberg'
        else:
            raise ValueError(f"Unsupported correction method: {correction}")

        result['adjusted_p_value'] = adj_p[0]
        result['significant'] = sig[0]

    return result