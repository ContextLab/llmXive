"""
Unit tests for chi_squared_utils module.

Verifies:
- Expected count calculation
- Low count detection
- Yates' correction trigger
- Fisher's Exact Test trigger
- Warning generation for non-2x2 low counts
"""

import numpy as np
import pytest
import warnings
from code.simulation.chi_squared_utils import (
    calculate_expected_counts,
    check_low_expected_counts,
    run_chi_squared_with_fallback
)


class TestExpectedCounts:
    def test_calculate_expected_counts_basic(self):
        """Test basic expected count calculation."""
        observed = np.array([[10, 20], [30, 40]])
        expected = calculate_expected_counts(observed)
        
        # Row totals: 30, 70. Col totals: 40, 60. Grand total: 100.
        # E[0,0] = (30 * 40) / 100 = 12
        # E[0,1] = (30 * 60) / 100 = 18
        # E[1,0] = (70 * 40) / 100 = 28
        # E[1,1] = (70 * 60) / 100 = 42
        expected_manual = np.array([[12.0, 18.0], [28.0, 42.0]])
        
        np.testing.assert_array_almost_equal(expected, expected_manual)

    def test_calculate_expected_counts_zero_total(self):
        """Test handling of zero total counts."""
        observed = np.array([[0, 0], [0, 0]])
        expected = calculate_expected_counts(observed)
        assert np.all(expected == 0)

class TestLowCountDetection:
    def test_check_low_expected_counts_no_low(self):
        """Test detection when no counts are low."""
        observed = np.array([[50, 50], [50, 50]])
        has_low, expected = check_low_expected_counts(observed)
        assert not has_low

    def test_check_low_expected_counts_has_low(self):
        """Test detection when counts are low."""
        observed = np.array([[1, 2], [3, 4]])
        has_low, expected = check_low_expected_counts(observed)
        assert has_low

class TestFallbackLogic:
    def test_yates_correction_trigger(self):
        """Test that Yates' correction is applied for 2x2 with expected < 5."""
        # Create a table where expected counts will be < 5
        # Total N=10. Expected roughly 2.5 per cell.
        observed = np.array([[2, 3], [1, 4]])
        result = run_chi_squared_with_fallback(observed)
        
        assert result['method'] == 'chi2_yates'
        assert result['pvalue'] is not None
        assert "Yates' correction" in result['warnings'][0]

    def test_fisher_exact_trigger(self):
        """Test that Fisher's Exact Test is applied for 2x2 with expected < 1."""
        # Create a table with very low counts
        observed = np.array([[0, 1], [1, 0]])
        result = run_chi_squared_with_fallback(observed)
        
        assert result['method'] == 'fisher_exact'
        assert result['statistic'] is None  # Fisher's doesn't return a chi2 stat
        assert result['pvalue'] is not None
        assert "Fisher's Exact Test" in result['warnings'][0]

    def test_standard_chi2_no_low_counts(self):
        """Test standard Chi-Squared when no low counts exist."""
        observed = np.array([[50, 50], [50, 50]])
        result = run_chi_squared_with_fallback(observed)
        
        assert result['method'] == 'chi2'
        assert "correction" not in result['method']
        assert len(result['warnings']) == 0

    def test_non_2x2_low_counts_warning(self):
        """Test warning for non-2x2 tables with low expected counts."""
        # 3x3 table with low counts
        observed = np.array([[1, 2, 1], [2, 1, 2], [1, 2, 1]])
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = run_chi_squared_with_fallback(observed)
            
            # Should trigger a warning
            assert len(result['warnings']) > 0
            assert "non-2x2" in result['warnings'][0].lower()
            
            # Should still return a result (standard chi2)
            assert result['method'] == 'chi2'
            assert result['pvalue'] is not None

    def test_invalid_shape_raises(self):
        """Test that 1D input raises ValueError."""
        observed = np.array([1, 2, 3, 4])
        with pytest.raises(ValueError, match="2-dimensional"):
            run_chi_squared_with_fallback(observed)