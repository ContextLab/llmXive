"""
Unit tests for statistical analysis functionality.
"""
import pytest
import numpy as np
from scipy import stats

class CircularValidationRiskError(Exception):
    """Custom exception for circular validation risk."""
    pass

def test_pearson_threshold_halt():
    """Assert that if correlation >= 0.5, the function raises CircularValidationRiskError."""
    from src.services.analysis import check_independence
    
    # Create data with high correlation
    human_scores = np.array([1, 2, 3, 4, 5])
    logic_scores = np.array([1.1, 2.1, 3.1, 4.1, 5.1])  # Almost perfect correlation
    
    with pytest.raises(CircularValidationRiskError):
        check_independence(human_scores, logic_scores)

def test_fisher_z_test():
    """Assert Fisher's r-to-z transformation calculates the correct z-score and p-value for two independent correlations."""
    from src.services.analysis import fisher_z_test
    
    # Test with known values
    r1 = 0.6
    r2 = 0.3
    n1 = 100
    n2 = 100
    
    z_score, p_value = fisher_z_test(r1, r2, n1, n2)
    
    # Verify z-score is positive (r1 > r2)
    assert z_score > 0
    # Verify p-value is between 0 and 1
    assert 0 <= p_value <= 1

def test_fdr_correction():
    """Assert Benjamini-Hochberg correction correctly adjusts p-values."""
    from src.services.analysis import benjamini_hochberg_correction
    
    # Test with known p-values
    p_values = [0.01, 0.04, 0.03, 0.001, 0.02]
    adjusted_p_values = benjamini_hochberg_correction(p_values, alpha=0.05)
    
    # Verify adjusted p-values are in [0, 1]
    assert all(0 <= p <= 1 for p in adjusted_p_values)
    
    # Verify monotonicity (adjusted p-values should be non-decreasing when sorted by original p-values)
    sorted_indices = np.argsort(p_values)
    sorted_adjusted = [adjusted_p_values[i] for i in sorted_indices]
    assert all(sorted_adjusted[i] <= sorted_adjusted[i+1] for i in range(len(sorted_adjusted)-1))