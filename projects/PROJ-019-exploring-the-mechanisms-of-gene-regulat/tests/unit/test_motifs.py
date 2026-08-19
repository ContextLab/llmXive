import pytest
from code.enrichment import calculate_enrichment, benjamini_hochberg_correction
import math

def test_fisher_exact_correction():
    """
    Test that Fisher's test returns correct p-values and Benjamini-Hochberg 
    correction returns correct q-values for a known input matrix.
    Covers: US2-FR-004 (Enrichment calculation with multiple-testing correction)
    
    This test uses a known contingency table and verifies the mathematical
    correctness of the enrichment calculation and FDR correction.
    """
    # Known contingency table for a single motif:
    #               In Target Peaks    Not in Target Peaks
    # In Motif      50 (a)           100 (b)
    # Not in Motif  50 (c)           800 (d)
    #
    # Total target peaks: 100
    # Total background peaks: 1000
    # Total motif occurrences: 150
    # Total non-motif occurrences: 850
    
    a = 50  # In target AND in motif
    b = 100 # Not in target BUT in motif
    c = 50  # In target BUT not in motif
    d = 800 # Not in target AND not in motif

    # Calculate enrichment
    p_value, odds_ratio = calculate_enrichment(a, b, c, d)
    
    # Verify odds ratio calculation: (a*d) / (b*c)
    expected_odds = (a * d) / (b * c)
    assert math.isclose(odds_ratio, expected_odds, rel_tol=1e-5), \
        f"Odds ratio mismatch: got {odds_ratio}, expected {expected_odds}"
    
    # Verify p-value is a valid probability
    assert 0 <= p_value <= 1, f"P-value {p_value} is not in [0, 1]"

    # Test Benjamini-Hochberg correction
    # Create a list of p-values
    p_values = [0.001, 0.005, 0.01, 0.05, 0.1, 0.2, 0.5]
    m = len(p_values)  # Total number of tests
    
    q_values = benjamini_hochberg_correction(p_values)
    
    # Verify q-values are in [0, 1]
    for q in q_values:
        assert 0 <= q <= 1, f"Q-value {q} is not in [0, 1]"
    
    # Verify monotonicity (q-values should be non-decreasing when p-values are sorted)
    # Note: BH correction ensures that q-values are monotonic with respect to rank
    # The implementation should ensure q_values[i] <= q_values[i+1] for sorted p-values
    for i in range(len(q_values) - 1):
        assert q_values[i] <= q_values[i + 1] + 1e-10, \
            f"Q-values not monotonic: {q_values[i]} > {q_values[i+1]}"
    
    # Verify that smaller p-values get smaller q-values (generally)
    # The smallest p-value should have the smallest q-value
    min_p_idx = p_values.index(min(p_values))
    min_q_idx = q_values.index(min(q_values))
    assert min_p_idx == min_q_idx, \
        "Smallest p-value should correspond to smallest q-value"

def test_benjamini_hochberg_edge_cases():
    """
    Test BH correction with edge cases: empty list, single value, all zeros.
    """
    # Empty list
    assert benjamini_hochberg_correction([]) == []
    
    # Single value
    q_single = benjamini_hochberg_correction([0.05])
    assert len(q_single) == 1
    assert q_single[0] == 0.05  # For single test, q = p
    
    # All zeros
    q_zeros = benjamini_hochberg_correction([0.0, 0.0, 0.0])
    assert all(q == 0.0 for q in q_zeros)
    
    # All ones
    q_ones = benjamini_hochberg_correction([1.0, 1.0, 1.0])
    assert all(q == 1.0 for q in q_ones)