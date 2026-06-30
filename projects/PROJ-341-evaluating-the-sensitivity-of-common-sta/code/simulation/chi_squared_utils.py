"""
Utilities for Chi-Squared test robustness.

Implements detection of expected cell counts < 5 and applies
Yates' continuity correction or Fisher's Exact Test as fallbacks.

FR-007 Compliance:
- Detects expected cell counts < 5
- Applies Yates' correction for 2x2 tables
- Falls back to Fisher's Exact Test for 2x2 tables with very low counts
- Issues warnings for non-2x2 tables with low counts
"""

import numpy as np
from scipy import stats
from typing import Tuple, Dict, Any, Optional
import warnings


def calculate_expected_counts(observed: np.ndarray) -> np.ndarray:
    """
    Calculate expected cell counts for a contingency table.
    
    Args:
        observed: 2D numpy array of observed counts.
        
    Returns:
        2D numpy array of expected counts.
    """
    row_totals = observed.sum(axis=1, keepdims=True)
    col_totals = observed.sum(axis=0, keepdims=True)
    grand_total = observed.sum()
    
    if grand_total == 0:
        return np.zeros_like(observed, dtype=float)
        
    expected = (row_totals * col_totals) / grand_total
    return expected


def check_low_expected_counts(observed: np.ndarray, threshold: float = 5.0) -> Tuple[bool, np.ndarray]:
    """
    Check if any expected cell counts are below the threshold.
    
    Args:
        observed: 2D numpy array of observed counts.
        threshold: Minimum expected count threshold (default 5.0).
        
    Returns:
        Tuple of (has_low_counts, expected_counts_array).
    """
    expected = calculate_expected_counts(observed)
    has_low = np.any(expected < threshold)
    return has_low, expected


def run_chi_squared_with_fallback(observed: np.ndarray, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run Chi-Squared test with automatic fallback logic for low expected counts.
    
    Logic:
    1. Calculate expected counts.
    2. If any expected count < 5:
       - If 2x2 table: Apply Yates' correction.
       - If 2x2 table AND any expected count < 1: Use Fisher's Exact Test.
       - If > 2x2 table: Issue warning, proceed with standard Chi-Squared (or user must handle).
    3. Return results including method used and any warnings.
    
    Args:
        observed: 2D numpy array of observed counts.
        alpha: Significance level (used for context, not calculation).
        
    Returns:
        Dictionary containing:
            - 'statistic': Test statistic (or None for Fisher's)
            - 'pvalue': P-value
            - 'method': String describing the method used ('chi2', 'chi2_yates', 'fisher_exact')
            - 'expected_counts': Array of expected counts
            - 'warnings': List of warning messages
            - 'degrees_of_freedom': Degrees of freedom (None for Fisher's)
    """
    result = {
        'statistic': None,
        'pvalue': None,
        'method': 'unknown',
        'expected_counts': None,
        'warnings': [],
        'degrees_of_freedom': None
    }
    
    # Validate input shape
    if observed.ndim != 2:
        raise ValueError("Observed table must be 2-dimensional.")
    
    rows, cols = observed.shape
    
    # Calculate expected counts
    has_low, expected = check_low_expected_counts(observed)
    result['expected_counts'] = expected
    
    # Check for 2x2 table
    is_2x2 = (rows == 2 and cols == 2)
    
    if has_low:
        min_expected = np.min(expected)
        
        if is_2x2:
            if min_expected < 1.0:
                # Use Fisher's Exact Test
                try:
                    # scipy.stats.fisher_exact returns (odds_ratio, p_value)
                    # 'two-sided' is the default
                    _, p_val = stats.fisher_exact(observed, alternative='two-sided')
                    result['pvalue'] = p_val
                    result['method'] = 'fisher_exact'
                    result['warnings'].append(
                        f"Fisher's Exact Test used due to expected count < 1 (min expected: {min_expected:.2f})."
                    )
                except Exception as e:
                    result['warnings'].append(f"Fisher's Exact Test failed: {str(e)}. Falling back to standard Chi-Squared.")
                    # Fallback to standard if Fisher fails
                    result['method'] = 'chi2'
                    stat, p_val, dof, exp = stats.chi2_contingency(observed, correction=False)
                    result['statistic'] = stat
                    result['pvalue'] = p_val
                    result['degrees_of_freedom'] = dof
            else:
                # Use Yates' correction
                stat, p_val, dof, exp = stats.chi2_contingency(observed, correction=True)
                result['statistic'] = stat
                result['pvalue'] = p_val
                result['degrees_of_freedom'] = dof
                result['method'] = 'chi2_yates'
                result['warnings'].append(
                    f"Yates' correction applied due to expected count < 5 (min expected: {min_expected:.2f})."
                )
        else:
            # Non-2x2 table with low expected counts
            # Standard practice is to warn and proceed, or suggest merging categories.
            # We proceed with standard Chi-Squared but warn heavily.
            warnings.warn(
                f"Expected cell counts < 5 detected in non-2x2 table. "
                f"Standard Chi-Squared test may be unreliable. Min expected: {min_expected:.2f}",
                RuntimeWarning
            )
            result['warnings'].append(
                f"Non-2x2 table with expected counts < 5. Results may be unreliable (min expected: {min_expected:.2f})."
            )
            stat, p_val, dof, exp = stats.chi2_contingency(observed, correction=False)
            result['statistic'] = stat
            result['pvalue'] = p_val
            result['degrees_of_freedom'] = dof
            result['method'] = 'chi2'
    else:
        # No low expected counts, standard test
        stat, p_val, dof, exp = stats.chi2_contingency(observed, correction=False)
        result['statistic'] = stat
        result['pvalue'] = p_val
        result['degrees_of_freedom'] = dof
        result['method'] = 'chi2'
    
    return result
