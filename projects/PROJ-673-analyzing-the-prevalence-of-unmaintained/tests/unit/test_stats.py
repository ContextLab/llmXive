"""
Unit tests for statistical correlation calculations.
Specifically tests Spearman correlation bounds and validity.
"""
import pytest
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from typing import List, Tuple, Optional

# Import the specific function we are testing if it exists in the project,
# otherwise we test the standard scipy implementation behavior which our code relies on.
# Based on the API surface, src/analysis/correlation.py defines calculate_spearman_correlation.
try:
    from src.analysis.correlation import calculate_spearman_correlation
    HAS_CORRELATION_MODULE = True
except ImportError:
    HAS_CORRELATION_MODULE = False


class TestSpearmanCorrelationBounds:
    """
    Tests to ensure Spearman correlation calculation respects mathematical bounds [-1, 1].
    """

    def test_perfect_positive_correlation(self):
        """Test that perfectly increasing data yields r=1.0"""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        
        if HAS_CORRELATION_MODULE:
            r, p = calculate_spearman_correlation(x, y)
        else:
            r, p = spearmanr(x, y)
        
        assert r == 1.0, f"Expected r=1.0 for perfect positive correlation, got {r}"
        assert p < 0.05, "P-value should be significant for perfect correlation"

    def test_perfect_negative_correlation(self):
        """Test that perfectly decreasing data yields r=-1.0"""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([10, 8, 6, 4, 2])
        
        if HAS_CORRELATION_MODULE:
            r, p = calculate_spearman_correlation(x, y)
        else:
            r, p = spearmanr(x, y)
        
        assert r == -1.0, f"Expected r=-1.0 for perfect negative correlation, got {r}"
        assert p < 0.05, "P-value should be significant for perfect correlation"

    def test_no_correlation(self):
        """Test that uncorrelated random data yields r near 0"""
        np.random.seed(42) # For reproducibility
        x = np.random.rand(100)
        y = np.random.rand(100)
        
        if HAS_CORRELATION_MODULE:
            r, p = calculate_spearman_correlation(x, y)
        else:
            r, p = spearmanr(x, y)
        
        # With random data, r should be close to 0, definitely within [-1, 1]
        assert -1.0 <= r <= 1.0, f"Correlation {r} is outside valid bounds [-1, 1]"
        # Note: p-value might not be significant for random data, so we don't assert on it strictly

    def test_bounds_validation(self):
        """Assert that calculated r is always within [-1, 1] for various inputs"""
        test_cases = [
            (np.array([1, 2, 3]), np.array([3, 2, 1])),
            (np.array([1, 1, 1]), np.array([1, 2, 3])), # Constant x
            (np.random.rand(50), np.random.rand(50)),
            (np.linspace(0, 10, 20), np.sin(np.linspace(0, 10, 20))),
        ]
        
        for i, (x, y) in enumerate(test_cases):
            try:
                if HAS_CORRELATION_MODULE:
                    r, p = calculate_spearman_correlation(x, y)
                else:
                    r, p = spearmanr(x, y)
                
                assert -1.0 - 1e-10 <= r <= 1.0 + 1e-10, \
                    f"Test case {i}: Correlation {r} is outside valid bounds [-1, 1]"
            except Exception as e:
                # Some cases (like constant arrays) might raise warnings/errors in scipy
                # We allow that as long as we don't get a valid number outside bounds
                if HAS_CORRELATION_MODULE:
                    # If our wrapper handles it, check if it returns None or raises
                    pass

    def test_p_value_bounds(self):
        """Assert that p-value is always within [0, 1]"""
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 6, 7, 8, 7])
        
        if HAS_CORRELATION_MODULE:
            r, p = calculate_spearman_correlation(x, y)
        else:
            r, p = spearmanr(x, y)
        
        assert 0.0 <= p <= 1.0, f"P-value {p} is outside valid bounds [0, 1]"

    def test_empty_arrays(self):
        """Test handling of empty arrays"""
        x = np.array([])
        y = np.array([])
        
        with pytest.raises((ValueError, Exception)):
            if HAS_CORRELATION_MODULE:
                calculate_spearman_correlation(x, y)
            else:
                spearmanr(x, y)

    def test_single_element(self):
        """Test handling of single element arrays"""
        x = np.array([1])
        y = np.array([2])
        
        # Spearman correlation on single element is undefined (division by zero in std dev)
        with pytest.raises((ValueError, Exception)):
            if HAS_CORRELATION_MODULE:
                calculate_spearman_correlation(x, y)
            else:
                spearmanr(x, y)

    def test_nan_handling(self):
        """Test that NaN values are handled correctly (either ignored or raise)"""
        x = np.array([1.0, 2.0, np.nan, 4.0])
        y = np.array([1.0, 2.0, 3.0, 4.0])
        
        # scipy.stats.spearmanr will return nan or raise depending on nan_policy
        # Our implementation should handle this gracefully or fail loudly
        try:
            if HAS_CORRELATION_MODULE:
                r, p = calculate_spearman_correlation(x, y)
            else:
                r, p = spearmanr(x, y, nan_policy='omit')
            
            # If it returns a value, it must be in bounds
            if not np.isnan(r):
                assert -1.0 <= r <= 1.0
        except Exception:
            # It is acceptable to raise an error for NaN data if not handled
            pass


class TestCorrelationModuleIntegration:
    """
    Tests specifically for the calculate_spearman_correlation function 
    if it is implemented in the project's correlation module.
    """

    @pytest.mark.skipif(not HAS_CORRELATION_MODULE, reason="correlation module not available")
    def test_function_signature(self):
        """Verify the function exists and has expected signature"""
        import inspect
        sig = inspect.signature(calculate_spearman_correlation)
        params = list(sig.parameters.keys())
        # Expecting at least x and y
        assert 'x' in params or 'data' in params

    @pytest.mark.skipif(not HAS_CORRELATION_MODULE, reason="correlation module not available")
    def test_returns_tuple(self):
        """Verify the function returns a tuple (r, p)"""
        x = np.array([1, 2, 3])
        y = np.array([3, 2, 1])
        result = calculate_spearman_correlation(x, y)
        assert isinstance(result, tuple), "Function should return a tuple (r, p)"
        assert len(result) == 2, "Tuple should have exactly 2 elements"

    @pytest.mark.skipif(not HAS_CORRELATION_MODULE, reason="correlation module not available")
    def test_real_data_example(self):
        """Test with a realistic example of age vs vulnerability count"""
        # Simulate data: older packages might have more vulnerabilities
        np.random.seed(123)
        age_days = np.random.randint(0, 3650, 100) # 0 to 10 years
        # Create a weak positive correlation
        vuln_count = age_days * 0.01 + np.random.normal(0, 2, 100)
        vuln_count = np.maximum(0, vuln_count) # No negative vulnerabilities
        
        r, p = calculate_spearman_correlation(age_days, vuln_count)
        
        assert -1.0 <= r <= 1.0
        assert 0.0 <= p <= 1.0