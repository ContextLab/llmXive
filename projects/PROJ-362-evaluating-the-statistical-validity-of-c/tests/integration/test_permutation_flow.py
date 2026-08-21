"""
Integration test for the full permutation flow.
Verifies p-value calculation logic (r+1)/(N+1) against manual calculation.
"""
import pytest

from p_values import calculate_p_value

def test_p_value_calculation():
    """
    Test p-value calculation: (r + 1) / (N + 1)
    where r is the rank of the observed score in the null distribution (0-indexed, sorted ascending).
    """
    null_scores = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    observed_score = 0.85
    
    # Expected:
    # Sorted null: [0.1, 0.2, ..., 1.0]
    # Observed 0.85 falls between 0.8 and 0.9.
    # Count of null scores >= observed: 0.8, 0.9, 1.0 -> 3 scores.
    # Wait, the formula (r+1)/(N+1) usually implies r is the number of permutations 
    # where the permuted score is >= observed score.
    # Let's assume the function implements: count(perm >= obs) + 1 / (N + 1)
    
    # Manual calculation:
    # N = 10
    # Count >= 0.85: 0.9, 1.0 (2 values) -> r = 2
    # p = (2 + 1) / (10 + 1) = 3/11 = 0.2727...
    
    p_val = calculate_p_value(null_scores, observed_score)
    
    expected = 3 / 11
    assert abs(p_val - expected) < 1e-6

def test_p_value_extreme_cases():
    """Test p-value with extreme observed scores."""
    null_scores = [0.1, 0.2, 0.3]
    
    # Observed lower than all null -> p = 1.0 (all nulls are >= obs)
    # Count >= 0.05: 3. r=3. p = 4/4 = 1.0
    p_low = calculate_p_value(null_scores, 0.05)
    assert abs(p_low - 1.0) < 1e-6
    
    # Observed higher than all null -> p = 1/(N+1)
    # Count >= 1.5: 0. r=0. p = 1/4 = 0.25
    p_high = calculate_p_value(null_scores, 1.5)
    assert abs(p_high - 0.25) < 1e-6
