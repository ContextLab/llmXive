import numpy as np
from scipy import stats
from typing import Tuple, Dict, Any, Optional
import warnings

def calculate_expected_counts(observed: np.ndarray) -> np.ndarray:
    """
    Calculate expected counts for a contingency table.
    
    Args:
        observed: 2D array of observed counts
        
    Returns:
        2D array of expected counts
    """
    row_totals = observed.sum(axis=1, keepdims=True)
    col_totals = observed.sum(axis=0, keepdims=True)
    grand_total = observed.sum()
    
    if grand_total == 0:
        return np.zeros_like(observed, dtype=float)
        
    expected = (row_totals * col_totals) / grand_total
    return expected

def check_low_expected_counts(expected: np.ndarray, threshold: float = 5.0) -> bool:
    """
    Check if any expected counts are below the threshold.
    
    Args:
        expected: 2D array of expected counts
        threshold: Minimum expected count threshold
        
    Returns:
        True if any expected count is below threshold
    """
    return np.any(expected < threshold)

def run_chi_squared_with_fallback(
    observed: np.ndarray,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run Chi-squared test with fallback to Yates' correction or Fisher's Exact Test.
    
    Args:
        observed: 2D array of observed counts
        alpha: Significance level
        
    Returns:
        Dictionary with p-value and test details
    """
    # Check for 2x2 table
    is_2x2 = observed.shape == (2, 2)
    
    # Calculate expected counts
    expected = calculate_expected_counts(observed)
    has_low_expected = check_low_expected_counts(expected)
    
    p_value = None
    test_used = "chi-squared"
    warning = None
    
    try:
        if is_2x2 and has_low_expected:
            # Use Yates' correction for continuity
            chi2, p_value, dof, exp = stats.chi2_contingency(observed, correction=True)
            test_used = "chi-squared (Yates)"
            warning = "Yates' correction applied due to low expected counts"
            
            # If expected counts are very low (< 5 in any cell), consider Fisher's
            if np.any(expected < 5):
                # Fisher's exact test
                oddsratio, p_value = stats.fisher_exact(observed)
                test_used = "Fisher's Exact"
                warning = "Fisher's Exact test applied due to very low expected counts"
        elif is_2x2:
            # Standard Chi-squared for 2x2
            chi2, p_value, dof, exp = stats.chi2_contingency(observed, correction=False)
        else:
            # Standard Chi-squared for larger tables
            chi2, p_value, dof, exp = stats.chi2_contingency(observed, correction=False)
            
    except Exception as e:
        return {
            'p_value': None,
            'error': str(e),
            'test_used': 'none'
        }
        
    return {
        'p_value': float(p_value) if p_value is not None else None,
        'test_used': test_used,
        'warning': warning,
        'expected_counts': expected.tolist()
    }
