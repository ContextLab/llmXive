"""
Tests for metrics.py module.

Specifically tests McNemar's test logic and coverage calculations.
"""
import pytest
import numpy as np
from metrics import (
    calculate_coverage,
    calculate_ci_width_stability,
    calculate_bias_block_bootstrap,
    mcnemar_test_logic,
    calculate_coverage_drop_magnitude
)


def test_mcnemar_test_logic_significant_difference():
    """
    Test McNemar's test logic with a known significant difference.
    
    Setup:
    - Ordered data has high coverage (e.g., 90%)
    - Shuffled data has high coverage (e.g., 90%)
    - BUT, we construct a scenario where they differ significantly in discordant pairs.
    
    We create a contingency table where:
    - Both covered: 800
    - Ordered covered, Shuffled not: 100
    - Ordered not, Shuffled covered: 10
    - Both not: 90
    
    Total: 1000
    Discordant pairs: 100 vs 10. This should yield a significant p-value.
    """
    # Construct the lists manually to match the table above
    # Both covered (800)
    ordered = [True] * 800
    shuffled = [True] * 800
    
    # Ordered covered, Shuffled not (100)
    ordered += [True] * 100
    shuffled += [False] * 100
    
    # Ordered not, Shuffled covered (10)
    ordered += [False] * 10
    shuffled += [True] * 10
    
    # Both not (90)
    ordered += [False] * 90
    shuffled += [False] * 90
    
    stat, p_value = mcnemar_test_logic(ordered, shuffled)
    
    # The statistic should be large (approx (100-10)^2 / (100+10) = 8100/110 ~ 73.6)
    assert stat > 50.0, f"Expected large statistic, got {stat}"
    assert p_value < 0.05, f"Expected p-value < 0.05, got {p_value}"


def test_mcnemar_test_logic_no_difference():
    """
    Test McNemar's test when there is no significant difference.
    
    Setup:
    - Balanced discordant pairs (e.g., 50 vs 50)
    """
    # Both covered: 800
    ordered = [True] * 800
    shuffled = [True] * 800
    
    # Discordant: 50 vs 50
    ordered += [True] * 50
    shuffled += [False] * 50
    
    ordered += [False] * 50
    shuffled += [True] * 50
    
    # Both not: 100
    ordered += [False] * 100
    shuffled += [False] * 100
    
    stat, p_value = mcnemar_test_logic(ordered, shuffled)
    
    # Statistic should be close to 0 ( (50-50)^2 / 100 = 0 )
    assert stat < 0.1, f"Expected small statistic, got {stat}"
    assert p_value > 0.05, f"Expected p-value > 0.05, got {p_value}"


def test_mcnemar_test_logic_empty_input():
    """Test McNemar's test with empty lists."""
    stat, p_value = mcnemar_test_logic([], [])
    assert stat == 0.0
    assert p_value == 1.0


def test_mcnemar_test_logic_length_mismatch():
    """Test McNemar's test raises error on mismatched lengths."""
    with pytest.raises(ValueError):
        mcnemar_test_logic([True, False], [True])


def test_coverage_degradation_at_high_phi():
    """
    Integration test for coverage calculation.
    
    Simulate a scenario where ordered data has low coverage and shuffled has high.
    """
    # Simulate 1000 trials
    # Ordered: 800 covered (80%)
    # Shuffled: 950 covered (95%)
    ordered_covered = [True] * 800 + [False] * 200
    shuffled_covered = [True] * 950 + [False] * 50
    
    ordered_cov = calculate_coverage([(0.9, 1.1) if c else (0.0, 0.5) for c in ordered_covered], 1.0)
    shuffled_cov = calculate_coverage([(0.9, 1.1) if c else (0.0, 0.5) for c in shuffled_covered], 1.0)
    
    # Verify coverage calculation
    assert abs(ordered_cov - 0.80) < 0.01
    assert abs(shuffled_cov - 0.95) < 0.01
    
    # Verify McNemar's test detects the difference
    stat, p_value = mcnemar_test_logic(ordered_covered, shuffled_covered)
    assert p_value < 0.05, f"Expected significant difference, got p={p_value}"


def test_ci_width_stability():
    """Test CI width stability calculation."""
    ordered_cis = [(0.8, 1.2), (0.9, 1.1), (0.7, 1.3)] # Widths: 0.4, 0.2, 0.6 -> Mean 0.4
    shuffled_cis = [(0.9, 1.1), (0.95, 1.05), (0.85, 1.15)] # Widths: 0.2, 0.1, 0.3 -> Mean 0.2
    
    ratio = calculate_ci_width_stability(ordered_cis, shuffled_cis)
    assert abs(ratio - 2.0) < 0.01


def test_bias_block_bootstrap():
    """Test bias calculation relative to block bootstrap."""
    ordered_cis = [(0.8, 1.2), (0.9, 1.1)] # Means: 1.0, 1.0 -> Avg 1.0
    block_cis = [(0.9, 1.1), (0.95, 1.05)] # Means: 1.0, 1.0 -> Avg 1.0
    
    bias = calculate_bias_block_bootstrap(ordered_cis, block_cis)
    assert bias == 0.0
    
    # Change block means
    block_cis = [(0.5, 0.9), (0.6, 1.0)] # Means: 0.7, 0.8 -> Avg 0.75
    bias = calculate_bias_block_bootstrap(ordered_cis, block_cis)
    assert abs(bias - 0.25) < 0.01


def test_coverage_drop_magnitude():
    """Test coverage drop magnitude calculation."""
    drop = calculate_coverage_drop_magnitude(0.80, 0.95)
    assert abs(drop - 0.15) < 0.001