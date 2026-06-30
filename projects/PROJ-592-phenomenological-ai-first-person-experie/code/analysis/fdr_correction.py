"""
Benjamini-Hochberg False Discovery Rate (FDR) Correction.

Implements the Benjamini-Hochberg procedure to control the expected proportion
of incorrectly rejected null hypotheses (false discoveries) when performing
multiple hypothesis tests.

This module is designed to be CPU-tractable and dependency-light (numpy, scipy),
suitable for the CI environment defined in T002/T004.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class FDRCorrectionError(Exception):
    """Custom exception for FDR correction failures."""
    pass


def benjamini_hochberg(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Apply the Benjamini-Hochberg FDR correction to a list of p-values.

    Args:
        p_values: A list of raw p-values from hypothesis tests.
        alpha: The desired False Discovery Rate threshold (default 0.05).

    Returns:
        A tuple containing:
        - rejected: A list of booleans indicating whether each hypothesis is rejected.
        - adjusted_p_values: A list of adjusted p-values (q-values).

    Raises:
        FDRCorrectionError: If input is invalid or computation fails.
    """
    if not p_values:
        logger.warning("Empty p-value list provided to FDR correction.")
        return [], []

    if not all(0.0 <= p <= 1.0 for p in p_values):
        raise FDRCorrectionError("All p-values must be between 0.0 and 1.0.")

    n = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = np.array([p_values[i] for i in sorted_indices])

    # Calculate adjusted p-values
    # Formula: p_adj[i] = p[i] * n / i
    # We use cumulative max to ensure monotonicity (step-up procedure)
    ranks = np.arange(1, n + 1)
    adjusted = (sorted_p_values * n) / ranks

    # Enforce monotonicity: p_adj[i] = min(p_adj[i], p_adj[i+1]) going backwards
    # Actually, standard BH ensures p_adj[i] <= p_adj[i+1] if sorted.
    # We need to ensure no adjusted p-value is smaller than the one before it in the sorted list.
    # Correct logic: iterate from largest rank to smallest, taking min with next.
    for i in range(n - 2, -1, -1):
        adjusted[i] = min(adjusted[i], adjusted[i + 1])

    # Clamp to [0, 1]
    adjusted = np.clip(adjusted, 0.0, 1.0)

    # Map back to original order
    final_adjusted = np.empty(n)
    final_adjusted[sorted_indices] = adjusted

    # Determine rejections
    rejected = final_adjusted <= alpha

    logger.debug(f"Applied BH FDR correction to {n} tests at alpha={alpha}. "
                 f"Rejections: {sum(rejected)}/{n}")

    return rejected.tolist(), final_adjusted.tolist()


def run_fdr_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, any]:
    """
    Orchestrate FDR correction and return a summary report.

    Args:
        p_values: List of p-values to correct.
        alpha: Significance threshold.

    Returns:
        Dictionary containing:
        - 'raw_p_values': Original p-values
        - 'adjusted_p_values': BH-corrected p-values
        - 'rejections': Boolean list of rejections
        - 'num_rejections': Count of rejected hypotheses
        - 'alpha': The threshold used
    """
    try:
        rejected, adjusted = benjamini_hochberg(p_values, alpha)

        return {
            'raw_p_values': p_values,
            'adjusted_p_values': adjusted,
            'rejections': rejected,
            'num_rejections': sum(rejected),
            'alpha': alpha
        }
    except Exception as e:
        logger.error(f"FDR correction failed: {e}")
        raise FDRCorrectionError(f"Failed to compute FDR correction: {e}") from e
