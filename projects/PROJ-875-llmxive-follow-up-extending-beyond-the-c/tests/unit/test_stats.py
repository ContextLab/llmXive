"""
Unit tests for code/stats.py statistical functions.
"""
import pytest
import numpy as np
from scipy import stats as scipy_stats
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.stats import mann_whitney_u_test, calculate_confidence_interval, aggregate_results


class TestMannWhitneyEdgeCases:
    """
    Edge case tests for Mann-Whitney U test implementation.
    These tests verify robustness against invalid or degenerate inputs.
    """

    def test_mann_whitney_empty(self):
        """
        Test behavior when input lists are empty.
        Expected: Should raise a ValueError or return a specific error indicator.
        """
        # Case 1: Both empty
        with pytest.raises((ValueError, IndexError)) as exc_info:
            mann_whitney_u_test([], [])
        
        # Verify error message mentions empty input
        assert "empty" in str(exc_info.value).lower() or "insufficient" in str(exc_info.value).lower()

        # Case 2: One empty, one non-empty
        with pytest.raises((ValueError, IndexError)) as exc_info:
            mann_whitney_u_test([], [1.0, 2.0, 3.0])
        
        assert "empty" in str(exc_info.value).lower() or "insufficient" in str(exc_info.value).lower()

    def test_mann_whitney_single(self):
        """
        Test behavior when one or both samples contain only a single value.
        Mann-Whitney U requires at least 2 observations to calculate variance/rank distribution.
        Expected: Should raise a ValueError or return a specific error indicator.
        """
        # Case 1: Both single
        with pytest.raises((ValueError, IndexError)) as exc_info:
            mann_whitney_u_test([1.0], [2.0])
        
        assert "single" in str(exc_info.value).lower() or "insufficient" in str(exc_info.value).lower()

        # Case 2: One single, one multiple
        with pytest.raises((ValueError, IndexError)) as exc_info:
            mann_whitney_u_test([1.0], [2.0, 3.0, 4.0])
        
        assert "single" in str(exc_info.value).lower() or "insufficient" in str(exc_info.value).lower()

    def test_mann_whitney_identical(self):
        """
        Test behavior when both samples contain identical values.
        Expected: Should return U=0 (or max), p=1.0 (no difference), and not crash.
        """
        sample_a = [5.0, 5.0, 5.0, 5.0]
        sample_b = [5.0, 5.0, 5.0, 5.0]

        # This should not raise an exception
        try:
            u_stat, p_val = mann_whitney_u_test(sample_a, sample_b)
            
            # Verify types
            assert isinstance(u_stat, (int, float, np.number))
            assert isinstance(p_val, (int, float, np.number))
            
            # For identical distributions, p-value should be 1.0 (or very close)
            # U statistic depends on implementation (min or max), but should be deterministic
            assert p_val == pytest.approx(1.0, abs=1e-6)
            
        except Exception as e:
            pytest.fail(f"Identical values test failed with exception: {e}")

    def test_mann_whitney_normal_case(self):
        """
        Sanity check: ensure normal operation still works after edge case handling added.
        """
        np.random.seed(42)
        sample_a = np.random.normal(loc=0.0, scale=1.0, size=50)
        sample_b = np.random.normal(loc=0.5, scale=1.0, size=50)

        u_stat, p_val = mann_whitney_u_test(sample_a, sample_b)

        assert isinstance(u_stat, (int, float, np.number))
        assert isinstance(p_val, (int, float, np.number))
        assert 0 <= p_val <= 1.0