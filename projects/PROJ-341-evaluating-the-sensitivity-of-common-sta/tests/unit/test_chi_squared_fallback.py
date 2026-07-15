import pytest
import numpy as np
from code.simulation.chi_squared_utils import run_chi_squared_with_fallback, check_low_expected_counts, calculate_expected_counts

def test_chi_squared_fallback_2x2():
    # Create a 2x2 table with low expected counts
    # Expected count = (row_sum * col_sum) / total
    # If we have small numbers, expected counts drop
    observed = np.array([[1, 4], [4, 1]]) # Total 10. Expected ~2.5
    expected = calculate_expected_counts(observed)
    assert check_low_expected_counts(expected)
    
    p_val, method = run_chi_squared_with_fallback(observed)
    assert method == "fisher_fallback"
    assert not np.isnan(p_val)

def test_chi_squared_standard():
    observed = np.array([[50, 50], [50, 50]])
    p_val, method = run_chi_squared_with_fallback(observed)
    assert method == "chi2_standard"

if __name__ == '__main__':
    pytest.main([__file__])