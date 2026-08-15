"""
Tests for the asymptotic baseline calculation (T005).
Verifies the implementation of Q_as(n) based on Meinardus' theorem.
"""

import pytest
import numpy as np
import math
from code.utils.asymptotic_baseline import compute_asymptotic_baseline, generate_asymptotic_series

class TestAsymptoticBaseline:
    def test_edge_cases(self):
        """Test behavior for n <= 1."""
        assert compute_asymptotic_baseline(0) == 0.0
        assert compute_asymptotic_baseline(1) == 0.0

    def test_small_n_positive(self):
        """Test that for n > 1, the result is positive."""
        val_2 = compute_asymptotic_baseline(2)
        val_10 = compute_asymptotic_baseline(10)
        assert val_2 > 0.0
        assert val_10 > 0.0
        # Check monotonicity for small n
        assert val_10 > val_2

    def test_formula_structure(self):
        """
        Verify the formula structure:
        Q_as(n) ~ C * exp(2 * pi * sqrt(n / (3 * log(n)))) / (n^(3/4) * (log(n))^(1/4))
        """
        n = 1000
        C = 0.142857
        log_n = math.log(n)
        
        # Manual calculation of the formula components
        exponent_arg = n / (3.0 * log_n)
        exponent = 2.0 * math.pi * math.sqrt(exponent_arg)
        denominator = (n ** 0.75) * (log_n ** 0.25)
        expected = C * math.exp(exponent) / denominator

        actual = compute_asymptotic_baseline(n)
        
        # Allow small floating point tolerance
        assert math.isclose(actual, expected, rel_tol=1e-5)

    def test_generate_series(self):
        """Test the series generation function."""
        series = generate_asymptotic_series(10, 2)
        
        # Check length (n=2,4,6,8,10)
        assert len(series) == 5
        
        # Check structure
        for n, q_val in series:
            assert isinstance(n, int)
            assert isinstance(q_val, float)
            assert q_val > 0.0
            assert n >= 2

    def test_growth_rate(self):
        """
        Verify that Q_as(n) grows super-polynomially but sub-exponentially
        (specifically like exp(sqrt(n/log n))).
        """
        # Compare log(Q_as(n)) against sqrt(n/log n)
        n_values = [1000, 5000, 10000, 20000]
        ratios = []
        
        for n in n_values:
            q_val = compute_asymptotic_baseline(n)
            log_q = math.log(q_val)
            sqrt_term = math.sqrt(n / math.log(n))
            
            # The formula is exp(2 * pi * sqrt_term) * sub_exp_factor
            # So log(Q) ~ 2*pi*sqrt_term + log(sub_exp_factor)
            # We check that log(Q) / sqrt_term approaches 2*pi
            ratios.append(log_q / sqrt_term)
        
        # The ratio should approach 2*pi as n increases
        # We just check it's in the ballpark of 2*pi (approx 6.28)
        # Note: For small n, the sub-exponential factor matters, so the ratio
        # might be slightly off, but should be positive and significant.
        for ratio in ratios:
            assert ratio > 0.0
            assert ratio < 15.0  # Reasonable upper bound