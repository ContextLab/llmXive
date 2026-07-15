import numpy as np
from scipy import stats
from typing import Tuple, Dict, Any, Optional
import warnings

def calculate_expected_counts(observed: np.ndarray) -> np.ndarray:
    """Calculate expected counts for chi-squared."""
    row_sums = observed.sum(axis=1, keepdims=True)
    col_sums = observed.sum(axis=0, keepdims=True)
    total = observed.sum()
    return (row_sums * col_sums) / total

def check_low_expected_counts(expected: np.ndarray, threshold: float = 5.0) -> bool:
    """Check if any expected count is below threshold."""
    return np.any(expected < threshold)

def run_chi_squared_with_fallback(observed: np.ndarray, alpha: float = 0.05) -> Tuple[float, str]:
    """Run chi-squared test, falling back to Fisher's Exact if expected counts are low."""
    try:
        expected = calculate_expected_counts(observed)
        if check_low_expected_counts(expected):
            # Fallback: Fisher's Exact for 2x2
            if observed.shape == (2, 2):
                _, p_val = stats.fisher_exact(observed)
                return p_val, "fisher_fallback"
            else:
                # For larger tables with low counts, warn and use chi-squared with correction
                warnings.warn("Low expected counts in chi-squared test. Using correction.")
                stat, p_val, _, _ = stats.chi2_contingency(observed, correction=True)
                return p_val, "chi2_corrected"
        else:
            stat, p_val, _, _ = stats.chi2_contingency(observed)
            return p_val, "chi2_standard"
    except Exception as e:
        return np.nan, f"error: {str(e)}"

if __name__ == '__main__':
    print("Chi-Squared Utils Module")
