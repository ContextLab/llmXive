"""Multiple testing correction module implementing Benjamini-Yekutieli procedure.

This module provides functions to control the False Discovery Rate (FDR)
under arbitrary dependence structures using the Benjamini-Yekutieli method.
"""
import numpy as np
from typing import List, Tuple, Dict, Any

def benjamini_yekutieli(p_values: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """Apply the Benjamini-Yekutieli procedure to a list of p-values.

    The BY procedure controls the FDR under arbitrary dependence of test statistics.
    It is more conservative than the BH procedure but robust to dependence.

    Args:
        p_values: Array of p-values to correct.
        alpha: Significance level (default 0.05).

    Returns:
        Tuple containing:
            - q_values: Adjusted q-values (FDR-corrected p-values).
            - is_significant: Boolean array indicating which hypotheses are significant.
    """
    n = len(p_values)
    if n == 0:
        return np.array([]), np.array([], dtype=bool)

    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]

    # Calculate the harmonic series sum for BY correction
    # c(m) = sum_{j=1}^{m} 1/j
    harmonic_sum = np.sum(1.0 / np.arange(1, n + 1))

    # Calculate critical values for BY
    critical_values = (np.arange(1, n + 1) / n) * (alpha / harmonic_sum)

    # Find the largest k such that p_(k) <= critical_value_(k)
    # We iterate from largest to smallest to find the threshold
    significant_mask = sorted_p <= critical_values

    if not np.any(significant_mask):
        # No significant results
        q_values = np.ones(n)
        is_significant = np.zeros(n, dtype=bool)
    else:
        # Find the largest index where condition holds
        k = np.max(np.where(significant_mask)[0])
        threshold = critical_values[k]

        # Calculate q-values (step-up procedure)
        q_values = np.ones(n)
        for i in range(n - 1, -1, -1):
            q_values[i] = min((n / (i + 1)) * sorted_p[i], q_values[i] if i < n - 1 else 1.0)
            # Ensure monotonicity
            if i < n - 1:
                q_values[i] = min(q_values[i], q_values[i + 1])

        # Assign q-values back to original order
        final_q_values = np.zeros(n)
        final_q_values[sorted_indices] = q_values

        # Determine significance
        is_significant = final_q_values <= alpha

    return final_q_values, is_significant


def apply_correction_to_results(
    results: List[Dict[str, Any]], alpha: float = 0.05
) -> List[Dict[str, Any]]:
    """Apply BY correction to a list of result dictionaries.

    Args:
        results: List of dictionaries containing 'p_value' keys.
        alpha: Significance level.

    Returns:
        Updated list of dictionaries with 'q_value' and 'is_significant' keys added.
    """
    if not results:
        return results

    p_values = np.array([r["p_value"] for r in results])
    q_values, is_significant = benjamini_yekutieli(p_values, alpha)

    for i, result in enumerate(results):
        result["q_value"] = q_values[i]
        result["is_significant"] = bool(is_significant[i])

    return results
