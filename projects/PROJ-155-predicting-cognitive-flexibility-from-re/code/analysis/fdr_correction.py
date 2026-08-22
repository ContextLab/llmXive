"""
FDR Correction Module for Post-hoc Network-Specific Analyses.

Implements the Benjamini-Hochberg (BH) procedure to control the False Discovery Rate (FDR)
at q <= 0.05 for multiple hypothesis testing. This is used for post-hoc analyses where
connectivity metrics are computed per network or edge rather than just globally.

This module provides functions to:
1. Apply BH correction to a list of p-values.
2. Determine significance status based on the corrected q-values.
3. Integrate with the existing regression pipeline for network-specific analyses.
"""

import os
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Union, Any

from code.data.paths import get_results_path, ensure_dir
from code.utils.logging import log_error, log_warning

logger = logging.getLogger(__name__)


def apply_bh_correction(p_values: Union[List[float], np.ndarray], 
                        q_threshold: float = 0.05) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Apply the Benjamini-Hochberg procedure to control the False Discovery Rate.

    Args:
        p_values: A list or array of raw p-values.
        q_threshold: The target FDR level (default 0.05).

    Returns:
        Tuple containing:
            - corrected_p_values (q-values): The adjusted p-values.
            - is_significant: Boolean array indicating if q <= q_threshold.
            - ranks: The rank of each p-value in the sorted list.
    
    Raises:
        ValueError: If p_values are not valid probabilities or array is empty.
    """
    if len(p_values) == 0:
        logger.warning("Empty p-value list provided to FDR correction.")
        return np.array([]), np.array([]), np.array([])

    p_array = np.asarray(p_values)
    
    # Validate p-values
    if np.any((p_array < 0) | (p_array > 1)):
        raise ValueError("All p-values must be between 0 and 1.")
    
    if np.any(np.isnan(p_array)):
        logger.warning("NaN values detected in p-values. Treating as non-significant.")
        # We will handle NaNs by keeping them NaN in the result, but they won't be significant
        # However, for sorting, we need to be careful.
        # Standard practice: NaNs are usually treated as 1.0 or excluded. 
        # Here we treat them as 1.0 for the rank calculation but keep them as NaN in output if needed,
        # or simply set their q-value to 1.0. Let's set them to 1.0 for the math.
        p_array_for_calc = p_array.copy()
        p_array_for_calc[np.isnan(p_array_for_calc)] = 1.0
    else:
        p_array_for_calc = p_array

    n = len(p_array_for_calc)
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_array_for_calc)
    sorted_p = p_array_for_calc[sorted_indices]
    
    # Calculate ranks (1-indexed)
    ranks = np.arange(1, n + 1)
    
    # Calculate BH critical values: (i/n) * q
    # But the standard BH procedure for q-values (adjusted p-values) is:
    # q_i = min( (n/i) * p_i, 1 )
    # And we enforce monotonicity: q_i = min(q_i, q_{i+1}) going backwards.
    
    # Step 1: Compute raw adjusted p-values
    # q = p * n / rank
    adjusted_p = sorted_p * n / ranks
    
    # Step 2: Enforce monotonicity (cumulative min from the end)
    # We iterate from the largest rank down to 1
    # q_i <= q_{i+1}
    for i in range(n - 2, -1, -1):
        if adjusted_p[i] > adjusted_p[i + 1]:
            adjusted_p[i] = adjusted_p[i + 1]
    
    # Clip to 1.0
    adjusted_p = np.minimum(adjusted_p, 1.0)
    
    # Restore original order
    # Create an array to hold the final q-values in original order
    q_values = np.zeros(n)
    q_values[sorted_indices] = adjusted_p
    
    # If there were NaNs in original, restore them as NaN (or 1.0 if preferred, but NaN is safer)
    # The calculation above set them to 1.0. Let's restore NaN if they were originally NaN.
    if np.any(np.isnan(p_array)):
        q_values[np.isnan(p_array)] = np.nan
    
    # Determine significance
    # Note: If p was NaN, q is NaN, and (NaN <= 0.05) is False, which is correct.
    is_sig = q_values <= q_threshold
    
    return q_values, is_sig, ranks


def run_fdr_correction_pipeline(p_values: List[float], 
                                feature_names: Optional[List[str]] = None,
                                q_threshold: float = 0.05,
                                output_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the FDR correction pipeline on a set of p-values.
    
    This function is designed for post-hoc network-specific analyses where
    multiple connections or networks are tested against the flexibility score.
    
    Args:
        p_values: List of raw p-values from hypothesis tests.
        feature_names: Optional list of feature names corresponding to p_values.
        q_threshold: FDR threshold (default 0.05).
        output_file: Optional path to save the results as CSV. If None, results are not saved.
    
    Returns:
        Dictionary containing:
            - 'raw_p_values': Original p-values
            - 'q_values': Adjusted p-values
            - 'is_significant': Boolean mask for significance
            - 'significant_count': Number of significant tests
            - 'total_count': Total number of tests
            - 'feature_names': (if provided) Names of the features
    """
    if not p_values:
        logger.warning("No p-values provided for FDR correction.")
        return {
            'raw_p_values': [],
            'q_values': [],
            'is_significant': [],
            'significant_count': 0,
            'total_count': 0,
            'feature_names': feature_names or []
        }
    
    q_values, is_sig, _ = apply_bh_correction(p_values, q_threshold)
    
    significant_count = int(np.sum(is_sig))
    total_count = len(p_values)
    
    result = {
        'raw_p_values': p_values,
        'q_values': q_values.tolist(),
        'is_significant': is_sig.tolist(),
        'significant_count': significant_count,
        'total_count': total_count,
        'feature_names': feature_names if feature_names else [f"Test_{i}" for i in range(total_count)]
    }
    
    if output_file:
        ensure_dir(os.path.dirname(output_file))
        df = pd.DataFrame({
            'Feature': result['feature_names'],
            'Raw_P_Value': result['raw_p_values'],
            'Q_Value': result['q_values'],
            'Significant': result['is_significant']
        })
        df.to_csv(output_file, index=False)
        logger.info(f"FDR correction results saved to {output_file}")
    
    return result


def main():
    """
    Example usage of the FDR correction module.
    This can be used as a standalone script to test the functionality
    or to run FDR correction on a specific set of results if needed.
    """
    # Example: Simulate p-values from a network-specific analysis
    # In a real scenario, these would come from testing each network/edge
    np.random.seed(42)
    n_tests = 100
    # Create some significant and some non-significant p-values
    p_values = np.random.uniform(0, 1, n_tests)
    # Force some to be significant
    p_values[:10] = np.random.uniform(0, 0.01, 10)
    
    feature_names = [f"Network_{i}" for i in range(n_tests)]
    
    output_path = os.path.join(get_results_path(), "fdr_network_analysis.csv")
    
    results = run_fdr_correction_pipeline(
        p_values=p_values,
        feature_names=feature_names,
        q_threshold=0.05,
        output_file=output_path
    )
    
    print(f"Total tests: {results['total_count']}")
    print(f"Significant tests (q <= 0.05): {results['significant_count']}")
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()