"""
Integration test for the full permutation flow.
Verifies p-value calculation logic (r+1)/(N+1) against manual calculation.
"""
import pytest
import sys
import os

# Ensure the code directory is in the path so we can import from code/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'projects', 'PROJ-362-evaluating-the-statistical-validity-of-c', 'code'))

from p_values import calculate_p_value

def test_p_value_calculation():
    """
    Test p-value calculation: (r + 1) / (N + 1)
    where r is the count of null scores >= observed score.
    """
    null_scores = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    observed_score = 0.85
    
    # Manual calculation:
    # N = 10
    # Count null scores >= 0.85: 0.9, 1.0 -> 2 values. So r = 2.
    # p = (2 + 1) / (10 + 1) = 3/11 = 0.272727...
    
    p_val = calculate_p_value(null_scores, observed_score)
    
    expected = 3 / 11
    assert abs(p_val - expected) < 1e-6, f"Expected {expected}, got {p_val}"

def test_p_value_extreme_cases():
    """Test p-value with extreme observed scores."""
    null_scores = [0.1, 0.2, 0.3]
    N = len(null_scores)
    
    # Case 1: Observed lower than all null -> all nulls are >= obs.
    # Count >= 0.05: 3 values. r = 3.
    # p = (3 + 1) / (3 + 1) = 4/4 = 1.0
    p_low = calculate_p_value(null_scores, 0.05)
    assert abs(p_low - 1.0) < 1e-6, f"Expected 1.0, got {p_low}"
    
    # Case 2: Observed higher than all null -> no nulls are >= obs.
    # Count >= 1.5: 0 values. r = 0.
    # p = (0 + 1) / (3 + 1) = 1/4 = 0.25
    p_high = calculate_p_value(null_scores, 1.5)
    assert abs(p_high - 0.25) < 1e-6, f"Expected 0.25, got {p_high}"
    
    # Case 3: Observed exactly equal to max null
    # Count >= 0.3: 1 value (0.3). r = 1.
    # p = (1 + 1) / (3 + 1) = 2/4 = 0.5
    p_equal = calculate_p_value(null_scores, 0.3)
    assert abs(p_equal - 0.5) < 1e-6, f"Expected 0.5, got {p_equal}"